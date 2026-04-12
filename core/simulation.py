"""
Simulation — the state machine for one doctor/patient/judge run.

``Simulation.create(experiment, profiles, repos)`` is the one entry point:
it builds the ``SimulationConfig``, inserts the row, renders prompts from
the experiment's current optimization target, wires the two ``AgentRuntime``s,
and returns a ready-to-run ``Simulation``. Call ``.start()`` to kick off the
async task (self-tracks under ``Simulation._active``) or ``await .run()`` to
drive it synchronously.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from typing import ClassVar

from core.agents.base import AgentRuntime
from core.agent import Agent as AgentConfig
from core.llm.factory import parse_provider_model
from core.repositories import RepoSet
from core.repositories.simulations import SimulationRepository
from core.logger import SimulationLogger
from core.types import (
    AgentStep,
    AgentTrace,
    ExperimentRecord,
    Message,
    Role,
    SimulationConfig,
    SimulationStatus,
    Transcript,
    TurnEndEvent,
    TurnStartEvent,
)

DEFAULT_MAX_TURNS = 8
DEFAULT_TURN_TIMEOUT = 120  # seconds

_DOCTOR_NAME = "doctor"
_PATIENT_NAME = "patient"


class Simulation:
    """One doctor/patient conversation driven by two ``AgentRuntime``s."""

    _active: ClassVar[dict[str, "Simulation"]] = {}

    def __init__(
        self,
        sim_repo: SimulationRepository,
        sim_id: str,
        doctor: AgentRuntime,
        patient: AgentRuntime,
        max_turns: int = DEFAULT_MAX_TURNS,
        logger: SimulationLogger | None = None,
    ):
        self.sim_repo = sim_repo
        self.sim_id = sim_id
        self.doctor = doctor
        self.patient = patient
        self.max_turns = max_turns
        self.logger = logger
        self.state = SimulationStatus.IDLE
        self.text_status = "Idle"
        self.trace = AgentTrace()
        self.transcript = Transcript()
        self._turn = 0
        self._pause_event = asyncio.Event()
        self._pause_event.set()
        self._subscribers: list[asyncio.Queue] = []
        self._task: asyncio.Task | None = None
        self.on_done: callable | None = None

    # ── Class-level construction ────────────────────────────────────────────

    @classmethod
    def create(
        cls,
        experiment: ExperimentRecord,
        profiles: dict[str, dict[str, str]],
        repos: RepoSet,
        *,
        logger: SimulationLogger | None = None,
        model: str | None = None,
        max_turns: int | None = None,
        draw_index: int | None = None,
    ) -> "Simulation":
        config = experiment.config
        resolved_model = model or config.model
        resolved_max_turns = max_turns if max_turns is not None else config.max_turns

        target_id = experiment.current_optimization_target_id
        if target_id is None:
            raise ValueError(f"Experiment {experiment.id} has no current optimization target")
        target = repos.optimization_targets.get(target_id)
        if target is None:
            raise ValueError(f"Optimization target {target_id} not found")

        sim_config = SimulationConfig(
            experiment_id=experiment.id,
            optimization_target_id=target.id,
            profiles={k: dict(v) for k, v in profiles.items()},
            model=resolved_model,
            max_turns=resolved_max_turns,
            draw_index=draw_index,
        )
        sim_record = repos.simulations.create(sim_config)

        merged_fields: dict[str, str] = {}
        for profile in profiles.values():
            merged_fields.update(profile)

        doctor_cfg = config.agent(_DOCTOR_NAME)
        patient_cfg = config.agent(_PATIENT_NAME)
        doctor_prompt = _render(doctor_cfg, target.prompts, merged_fields)
        patient_prompt = _render(patient_cfg, target.prompts, merged_fields)

        doctor_provider, doctor_model = parse_provider_model(doctor_cfg.model or resolved_model)
        patient_provider, patient_model = parse_provider_model(patient_cfg.model or resolved_model)

        doctor_runtime = AgentRuntime(doctor_provider, doctor_model, doctor_prompt, name=_DOCTOR_NAME)
        patient_runtime = AgentRuntime(patient_provider, patient_model, patient_prompt, name=_PATIENT_NAME)

        if logger is not None:
            logger.open(
                sim_record.id,
                experiment_id=experiment.id,
                experiment_name=config.name,
                optimization_target_id=target.id,
                model=resolved_model,
                max_turns=resolved_max_turns,
                profiles={k: dict(v) for k, v in profiles.items()},
                system_prompts={
                    _DOCTOR_NAME: doctor_prompt,
                    _PATIENT_NAME: patient_prompt,
                },
            )

        return cls(
            repos.simulations,
            sim_record.id,
            doctor_runtime,
            patient_runtime,
            max_turns=resolved_max_turns,
            logger=logger,
        )

    @classmethod
    def get_active(cls, sim_id: str) -> "Simulation | None":
        return cls._active.get(sim_id)

    @classmethod
    def active_count(cls) -> int:
        return len(cls._active)

    # ── State transitions ───────────────────────────────────────────────────

    @property
    def turn(self) -> int:
        return self._turn

    @property
    def is_finished(self) -> bool:
        return self.state in (SimulationStatus.COMPLETED, SimulationStatus.ERROR)

    def _broadcast(self, event: tuple[str, object]) -> None:
        for q in self._subscribers:
            q.put_nowait(event)

    async def subscribe(self) -> AsyncGenerator[tuple[str, object], None]:
        q: asyncio.Queue = asyncio.Queue()
        self._subscribers.append(q)
        try:
            while True:
                event = await q.get()
                if event is None:
                    break
                yield event
        finally:
            self._subscribers.remove(q)

    def start(self) -> None:
        """Spawn the run loop as an asyncio task and register under ``_active``."""
        Simulation._active[self.sim_id] = self
        previous_on_done = self.on_done

        def _cleanup() -> None:
            Simulation._active.pop(self.sim_id, None)
            if previous_on_done:
                previous_on_done()

        self.on_done = _cleanup
        self._task = asyncio.create_task(self._run_loop())

    async def _run_loop(self) -> None:
        try:
            async for event in self.run_streaming():
                self._broadcast(event)
        finally:
            self._broadcast(None)
            if self.on_done:
                self.on_done()

    def pause(self):
        if self.state != SimulationStatus.RUNNING:
            raise RuntimeError(f"Cannot pause from {self.state.value} (must be running)")
        self.state = SimulationStatus.PAUSED
        self.text_status = f"Paused at turn {self._turn + 1}/{self.max_turns}"
        self._pause_event.clear()

    def resume(self):
        if self.state != SimulationStatus.PAUSED:
            raise RuntimeError(f"Cannot resume from {self.state.value} (must be paused)")
        self.state = SimulationStatus.RUNNING
        self.text_status = f"Resuming turn {self._turn + 1}/{self.max_turns}"
        self._pause_event.set()

    def stop(self):
        if self.state not in (SimulationStatus.RUNNING, SimulationStatus.PAUSED):
            raise RuntimeError(f"Cannot stop from {self.state.value} (must be running or paused)")
        self.state = SimulationStatus.COMPLETED
        self.text_status = f"Stopped at turn {self._turn}/{self.max_turns}"
        self._pause_event.set()

    # ── Run loop ────────────────────────────────────────────────────────────

    async def run(self) -> AgentTrace:
        async for _ in self.run_streaming():
            pass
        return self.trace

    async def step(self) -> AgentStep:
        if self.state == SimulationStatus.IDLE:
            self.state = SimulationStatus.PAUSED
        if self._turn >= self.max_turns:
            self.state = SimulationStatus.COMPLETED
            raise RuntimeError("All turns completed")
        self.resume()
        step = None
        async for et, data in self._stream_turn(*self._next_turn()):
            if et == "turn_end":
                step = self.trace.steps[-1]
        if self._turn >= self.max_turns:
            self.state = SimulationStatus.COMPLETED
        else:
            self.state = SimulationStatus.PAUSED
        return step

    async def run_streaming(self) -> AsyncGenerator[tuple[str, object], None]:
        self.state = SimulationStatus.RUNNING
        self.text_status = "Starting..."
        try:
            while self._turn < self.max_turns:
                await self._pause_event.wait()
                if self.state in (SimulationStatus.COMPLETED, SimulationStatus.ERROR):
                    break
                role, agent = self._next_turn()
                self.text_status = f"Turn {self._turn + 1}/{self.max_turns} — {role.value.capitalize()} is responding..."
                messages = self.transcript.as_perspective(role.value)
                if not messages:
                    messages = [{"role": "user", "content": "Please explain my test results to me."}]
                async for event in self._stream_turn(role, agent, messages):
                    yield event
                if self.state == SimulationStatus.ERROR:
                    break
            if self.state == SimulationStatus.RUNNING:
                self.state = SimulationStatus.COMPLETED
        except Exception:
            self.state = SimulationStatus.ERROR
            raise
        finally:
            if self.state == SimulationStatus.COMPLETED:
                self.text_status = f"Completed ({self._turn} turns)"
                self.sim_repo.complete(self.sim_id, self.trace.duration_ms)
            elif self.state == SimulationStatus.ERROR:
                self.text_status = "Error"
                self.sim_repo.fail(self.sim_id)
            else:
                self.state = SimulationStatus.ERROR
                self.text_status = "Error"
                self.sim_repo.fail(self.sim_id)
        yield ("done", None)

    async def _stream_turn(
        self,
        role: Role,
        agent: AgentRuntime,
        messages: list[dict] | None = None,
    ) -> AsyncGenerator[tuple[str, object], None]:
        if messages is None:
            messages = self.transcript.as_perspective(role.value)
        current_turn = self._turn
        yield ("turn_start", TurnStartEvent(role=role.value, turn=current_turn))

        started_at = datetime.now(timezone.utc)
        input_messages = [Message(**m) for m in messages]
        chunks: list[str] = []

        try:
            async with asyncio.timeout(DEFAULT_TURN_TIMEOUT):
                async for token in agent.stream(messages):
                    chunks.append(token)
                    yield ("token", token)
        except (TimeoutError, Exception) as e:
            self.state = SimulationStatus.ERROR
            yield ("turn_error", {"role": role.value, "turn": current_turn, "error": str(e)})
            return

        output = "".join(chunks)
        ended_at = datetime.now(timezone.utc)
        duration_ms = (ended_at - started_at).total_seconds() * 1000

        step = AgentStep(
            agent_type=agent.agent_type,
            model=agent.model,
            system_prompt=agent.system_prompt,
            input_messages=input_messages,
            output=output,
            started_at=started_at,
            ended_at=ended_at,
            duration_ms=duration_ms,
            error=None,
        )
        self.transcript.add(role.value, output)
        self.trace.add(step)
        self._turn += 1

        self.sim_repo.add_turn(
            simulation_id=self.sim_id,
            turn_number=current_turn,
            role=role.value,
            agent_type=step.agent_type,
            content=step.output,
            duration_ms=step.duration_ms,
        )

        if self.logger:
            self.logger.log_turn(
                self.sim_id,
                turn=current_turn,
                role=role.value,
                input_messages=messages,
                output=output,
                duration_ms=duration_ms,
            )

        yield ("turn_end", TurnEndEvent(role=role.value, turn=current_turn))

    def _next_turn(self) -> tuple[Role, AgentRuntime]:
        if self._turn % 2 == 0:
            return Role.DOCTOR, self.doctor
        return Role.PATIENT, self.patient


def _render(agent: AgentConfig, target_prompts: dict[str, str], fields: dict[str, str]) -> str:
    """Use the target's prompt for this agent if present; otherwise the agent's seed prompt."""
    template = target_prompts.get(agent.name, agent.prompt)
    try:
        return template.format(**fields)
    except KeyError as exc:
        missing = exc.args[0]
        raise ValueError(
            f"Missing field {missing!r} while rendering prompt for agent {agent.name!r}"
        ) from exc
