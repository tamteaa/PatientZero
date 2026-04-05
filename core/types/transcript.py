from dataclasses import dataclass, field

from core.types.message import Message


@dataclass
class Transcript:
    """Ordered sequence of messages in a doctor/patient conversation."""

    messages: list[Message] = field(default_factory=list)

    def add(self, role: str, content: str) -> None:
        self.messages.append(Message(role=role, content=content))

    def to_dicts(self) -> list[dict]:
        """Serialize for JSON / LLM consumption."""
        return [{"role": m.role, "content": m.content} for m in self.messages]

    def as_perspective(self, speaker: str) -> list[dict]:
        """Build LLM message list from a speaker's perspective.

        The speaker's messages become 'assistant', others become 'user'.
        """
        return [
            {"role": "assistant" if m.role == speaker else "user", "content": m.content}
            for m in self.messages
        ]

    def __len__(self) -> int:
        return len(self.messages)

    def __iter__(self):
        return iter(self.messages)
