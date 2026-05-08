from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from app.models import AuditEvent

if TYPE_CHECKING:
    from app.observers import AgentObservationState


class Observer(Protocol):
    async def handle(self, event: AuditEvent, state: "AgentObservationState") -> list[AuditEvent]:
        ...


class EventBus:
    def __init__(self, observers: list[Observer]) -> None:
        self.observers = observers

    async def publish(self, event: AuditEvent, state: "AgentObservationState") -> list[AuditEvent]:
        generated: list[AuditEvent] = []
        for observer in self.observers:
            generated.extend(await observer.handle(event, state))
        return generated

