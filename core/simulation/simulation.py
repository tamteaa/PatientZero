from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from core.agents.base import Agent
from core.db.database import Database
from core.db.queries.simulations import (
    add_simulation_turn,
    complete_simulation,
    fail_simulation,
)
from core.types import (
    AgentStep,
    AgentTrace,
    Message,
    Role,
    SimulationStatus,
    Transcript,
    TurnEndEvent,
    TurnStartEvent,
)

if TYPE_CHECKING:
    from core.services.logger import SimulationLogger

DEFAULT_MAX_TURNS = 8
DEFAULT_TURN_TIMEOUT = 120  # seconds


class Simulation:
    def __init__(
        self,
        db: Database,
        sim_id: str,
        doctor: Agent,
        patient: Agent,
        max_turns: int = DEFAULT_MAX_TURNS,
        logger: SimulationLogger | None = None,
    ):
        self.db = db
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
        self._task = asyncio.create_task(self._run_loop())

    async def _run_loop(self) -> None:
        try:
            async for event in self.run_streaming():
                self._broadcast(event)
        finally:
            self._broadcast(None)  # sentinel to close subscribers
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
                complete_simulation(self.db, self.sim_id, self.trace.duration_ms)
            elif self.state == SimulationStatus.ERROR:
                self.text_status = "Error"
                fail_simulation(self.db, self.sim_id)
            else:
                # Cancelled or other exit while still RUNNING/PAUSED — avoid zombie `running` rows.
                self.state = SimulationStatus.ERROR
                self.text_status = "Error"
                fail_simulation(self.db, self.sim_id)
        yield ("done", None)

    async def _stream_turn(
        self,
        role: Role,
        agent: Agent,
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

        add_simulation_turn(
            self.db,
            sim_id=self.sim_id,
            turn_number=current_turn,
            role=role.value,
            agent_type=step.agent_type,
            content=step.output,
            duration_ms=step.duration_ms,
        )

        if self.logger:
            self.logger.log_turn(self.sim_id, current_turn, role.value, output, duration_ms)
            self.logger.log_turn_detail(
                self.sim_id, current_turn, role.value,
                agent.system_prompt, messages, output, duration_ms,
            )

        yield ("turn_end", TurnEndEvent(role=role.value, turn=current_turn))

    def _next_turn(self) -> tuple[Role, Agent]:
        if self._turn % 2 == 0:
            return Role.DOCTOR, self.doctor
        return Role.PATIENT, self.patient
