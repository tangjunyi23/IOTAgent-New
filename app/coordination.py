from __future__ import annotations

import json
import time
from pathlib import Path

from app.models import AgentMessage


class AgentMailbox:
    def __init__(self, directory: str | Path) -> None:
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def publish(
        self,
        *,
        session_id: str,
        sender_task_id: str,
        sender_role: str,
        stage: str,
        message_kind: str = "update",
        topic: str | None = None,
        recipients: list[str] | None = None,
        requires_response: bool = False,
        in_reply_to: str | None = None,
        content: str,
    ) -> AgentMessage:
        message = AgentMessage(
            session_id=session_id,
            sender_task_id=sender_task_id,
            sender_role=sender_role,
            stage=stage,
            message_kind=message_kind,
            topic=topic,
            recipients=recipients or [],
            requires_response=requires_response,
            in_reply_to=in_reply_to,
            content=content,
        )
        path = self.directory / f"{time.time_ns()}-{message.id}.json"
        tmp_path = path.with_suffix(".tmp")
        tmp_path.write_text(
            json.dumps(message.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        tmp_path.replace(path)
        return message

    def drain_for_peer(
        self,
        *,
        recipient_task_id: str,
        recipient_role: str,
        seen_message_ids: set[str],
    ) -> list[AgentMessage]:
        messages: list[AgentMessage] = []
        for path in sorted(self.directory.glob("*.json")):
            message = AgentMessage.model_validate(json.loads(path.read_text(encoding="utf-8")))
            if message.sender_task_id == recipient_task_id:
                continue
            if message.recipients and recipient_role not in message.recipients:
                continue
            if message.id in seen_message_ids:
                continue
            seen_message_ids.add(message.id)
            messages.append(message)
        return messages
