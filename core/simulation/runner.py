import asyncio
from collections.abc import AsyncGenerator
from datetime import datetime, timezone

from core.agents.base import Agent
from core.agents.explainer import ExplainerAgent
from core.agents.patient import PatientAgent
from core.types import (
    AgentStep,
    AgentTrace,
    Message,
    SimulationStatus,
    TurnEndEvent,
    TurnStartEvent,
)


class Simulation:
    """Orchestrates an explainer/patient simulation with state machine control."""

    def __init__(
        self,
        explainer: ExplainerAgent,
        patient: PatientAgent,
        mode: str,
    ):
        self.explainer = explainer
        self.patient = patient
        self.mode = mode
        self.max_turns = 2 if mode == "static" else 8
        self.state = SimulationStatus.IDLE
        self.trace = AgentTrace()
        self._transcript: list[Message] = []
        self._turn = 0
        self._pause_event = asyncio.Event()
        self._pause_event.set()

    @property
    def turn(self) -> int:
        return self._turn

    @property
    def is_finished(self) -> bool:
        return self.state in (SimulationStatus.COMPLETED, SimulationStatus.ERROR)

    # ── State transitions ────────────────────────────────────────────────

    def pause(self) -> None:
        """Pause after the current turn completes."""
        if self.state == SimulationStatus.RUNNING:
            self.state = SimulationStatus.PAUSED
            self._pause_event.clear()

    def resume(self) -> None:
        """Resume a paused simulation."""
        if self.state == SimulationStatus.PAUSED:
            self.state = SimulationStatus.RUNNING
            self._pause_event.set()

    def stop(self) -> None:
        """Stop from PAUSED state."""
        if self.state == SimulationStatus.PAUSED:
            self.state = SimulationStatus.COMPLETED
            self._pause_event.set()

    # ── Execution ────────────────────────────────────────────────────────

    async def run(self) -> AgentTrace:
        """Run all turns to completion, respecting pause/resume."""
        self.state = SimulationStatus.RUNNING

        while self._turn < self.max_turns:
            await self._pause_event.wait()

            if self.state == SimulationStatus.COMPLETED:
                break

            try:
                step = await self._execute_turn()
            except Exception:
                break

            self.trace.add(step)
            self._turn += 1

        if self.state == SimulationStatus.RUNNING:
            self.state = SimulationStatus.COMPLETED

        return self.trace

    async def step(self) -> AgentStep:
        """Execute exactly one turn, then pause."""
        if self.state == SimulationStatus.IDLE:
            self.state = SimulationStatus.PAUSED

        if self._turn >= self.max_turns:
            self.state = SimulationStatus.COMPLETED
            raise RuntimeError("All turns completed")

        step = await self._execute_turn()
        self.trace.add(step)
        self._turn += 1

        if self._turn >= self.max_turns:
            self.state = SimulationStatus.COMPLETED
        else:
            self.state = SimulationStatus.PAUSED

        return step

    async def run_streaming(
        self,
    ) -> AsyncGenerator[tuple[str, str | TurnStartEvent | TurnEndEvent | AgentStep | None], None]:
        """Run all turns, yielding streaming events.

        Yields:
            ("turn_start", TurnStartEvent)
            ("token", str)
            ("turn_end", TurnEndEvent)
            ("done", None)
        """
        self.state = SimulationStatus.RUNNING

        while self._turn < self.max_turns:
            await self._pause_event.wait()
            if self.state == SimulationStatus.COMPLETED:
                break

            speaker, agent = self._next_turn()
            current_turn = self._turn

            yield ("turn_start", TurnStartEvent(role=speaker, turn=current_turn))

            messages = self._build_messages(speaker)
            started_at = datetime.now(timezone.utc)
            input_messages = [Message(**m) for m in messages]

            error = None
            chunks: list[str] = []
            try:
                async for token in agent.stream(messages):
                    chunks.append(token)
                    yield ("token", token)
            except Exception as e:
                error = str(e)
                self.state = SimulationStatus.ERROR

            output = "".join(chunks)
            ended_at = datetime.now(timezone.utc)
            duration_ms = (ended_at - started_at).total_seconds() * 1000

            step = AgentStep(
                agent_type=type(agent).__name__,
                model=agent.model,
                system_prompt=agent.system_prompt,
                input_messages=input_messages,
                output=output,
                started_at=started_at,
                ended_at=ended_at,
                duration_ms=duration_ms,
                error=error,
            )

            self._transcript.append(Message(role=speaker, content=output))
            self.trace.add(step)
            self._turn += 1

            yield ("turn_end", TurnEndEvent(role=speaker, turn=current_turn))

            if self.state == SimulationStatus.ERROR:
                break

        if self.state == SimulationStatus.RUNNING:
            self.state = SimulationStatus.COMPLETED

        yield ("done", None)

    # ── Internal ─────────────────────────────────────────────────────────

    def _next_turn(self) -> tuple[str, Agent]:
        if self._turn % 2 == 0:
            return "explainer", self.explainer
        return "patient", self.patient

    def _build_messages(self, perspective: str) -> list[dict]:
        """Build message list from the given agent's perspective."""
        messages = []
        for msg in self._transcript:
            role = "assistant" if msg.role == perspective else "user"
            messages.append({"role": role, "content": msg.content})
        return messages

    async def _execute_turn(self) -> AgentStep:
        speaker, agent = self._next_turn()
        messages = self._build_messages(speaker)
        try:
            step = await agent.respond(messages)
            self._transcript.append(Message(role=speaker, content=step.output))
            return step
        except Exception:
            self.state = SimulationStatus.ERROR
            raise
