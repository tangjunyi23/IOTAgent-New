from __future__ import annotations

import asyncio
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from app.models import AuditEvent, AuditSession, ToolCapability


@dataclass
class AuditSubscription:
    broker: "AuditEventBroker"
    queue: asyncio.Queue[dict[str, Any]]
    session_id: str | None

    async def recv(self) -> dict[str, Any]:
        return await self.queue.get()

    async def close(self) -> None:
        await self.broker.unsubscribe(self)


class AuditEventBroker:
    def __init__(self) -> None:
        self._global_subscribers: set[asyncio.Queue[dict[str, Any]]] = set()
        self._session_subscribers: dict[str, set[asyncio.Queue[dict[str, Any]]]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def subscribe(self, session_id: str | None = None) -> AuditSubscription:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=256)
        async with self._lock:
            if session_id is None:
                self._global_subscribers.add(queue)
            else:
                self._session_subscribers[session_id].add(queue)
        return AuditSubscription(broker=self, queue=queue, session_id=session_id)

    async def unsubscribe(self, subscription: AuditSubscription) -> None:
        async with self._lock:
            if subscription.session_id is None:
                self._global_subscribers.discard(subscription.queue)
            else:
                subscribers = self._session_subscribers.get(subscription.session_id)
                if subscribers is not None:
                    subscribers.discard(subscription.queue)
                    if not subscribers:
                        self._session_subscribers.pop(subscription.session_id, None)

    async def publish_event(
        self,
        session_id: str,
        event: AuditEvent,
        task_id: str | None = None,
    ) -> None:
        await self._broadcast(
            {
                "type": "audit_event",
                "session_id": session_id,
                "task_id": task_id,
                "event": event.model_dump(mode="json"),
            },
            session_id=session_id,
        )

    async def publish_snapshot(self, session: AuditSession) -> None:
        await self._broadcast(
            {
                "type": "session_snapshot",
                "session_id": session.id,
                "session": session.model_dump(mode="json"),
            },
            session_id=session.id,
        )

    async def publish_tool_inventory(self, inventory: list[ToolCapability]) -> None:
        await self._broadcast(
            {
                "type": "tool_inventory",
                "tool_capabilities": [item.model_dump(mode="json") for item in inventory],
            },
            session_id=None,
        )

    async def _broadcast(self, message: dict[str, Any], session_id: str | None) -> None:
        async with self._lock:
            targets = set(self._global_subscribers)
            if session_id is not None:
                targets.update(self._session_subscribers.get(session_id, set()))

        for queue in targets:
            self._put_nowait(queue, message)

    def _put_nowait(self, queue: asyncio.Queue[dict[str, Any]], message: dict[str, Any]) -> None:
        while True:
            try:
                queue.put_nowait(message)
                return
            except asyncio.QueueFull:
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    return

