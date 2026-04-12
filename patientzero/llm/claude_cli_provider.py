import asyncio
import json
from collections.abc import AsyncGenerator

from patientzero.llm.base import LLMProvider


class ClaudeCLIProvider(LLMProvider):
    """Provider that shells out to the `claude` CLI."""

    async def stream(self, messages: list[dict], model: str) -> AsyncGenerator[str, None]:
        system_prompt = None
        conversation: list[dict] = []
        for msg in messages:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            else:
                conversation.append(msg)

        # Build a plain text prompt from the conversation history
        parts = []
        for msg in conversation:
            label = "Human" if msg["role"] == "user" else "Assistant"
            parts.append(f"{label}: {msg['content']}")
        prompt = "\n\n".join(parts)

        cmd = [
            "claude", "-p",
            "--no-session-persistence",
            "--tools", "",
            "--output-format", "stream-json",
        ]
        if model and model != "default":
            cmd.extend(["--model", model])
        if system_prompt:
            cmd.extend(["--system-prompt", system_prompt])

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd="/tmp",
        )

        proc.stdin.write(prompt.encode())
        proc.stdin.close()

        emitted = 0  # characters already yielded
        async for line in proc.stdout:
            line = line.decode().strip()
            if not line:
                continue
            try:
                event = json.loads(line)
                # Each "assistant" event contains cumulative text — only yield the new delta
                if event.get("type") == "assistant":
                    msg = event.get("message", {})
                    full_text = "".join(
                        block["text"]
                        for block in msg.get("content", [])
                        if block.get("type") == "text"
                    )
                    if len(full_text) > emitted:
                        yield full_text[emitted:]
                        emitted = len(full_text)
            except json.JSONDecodeError:
                continue

        await proc.wait()
        if proc.returncode != 0:
            stderr = await proc.stderr.read()
            raise RuntimeError(f"claude CLI exited {proc.returncode}: {stderr.decode().strip()}")
