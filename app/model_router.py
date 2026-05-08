from __future__ import annotations

from pydantic import BaseModel

from app.config import Settings
from app.models import AuditRequest, DifficultyHint


class ModelSelection(BaseModel):
    model: str
    thinking_enabled: bool = True
    reasoning_effort: str = "high"
    route_reason: str


class ModelRouter:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def select_for_subagent(self, request: AuditRequest, role: str) -> ModelSelection:
        return self.select_for_subagent_phase(request, role, phase="summary")

    def select_for_subagent_phase(
        self,
        request: AuditRequest,
        role: str,
        *,
        phase: str,
        round_index: int = 1,
        has_history: bool = False,
        objective: str | None = None,
    ) -> ModelSelection:
        difficulty = request.difficulty
        hard_roles = {"dynamic-analysis", "exploit-strategy", "exploitability-review"}
        hard_keywords = ("heap", "race", "kernel", "sandbox", "vm", "jit", "复杂", "链", "提权")
        normalized_objective = (objective or request.objective or "").lower()
        force_hard = role in hard_roles or any(keyword in normalized_objective for keyword in hard_keywords)

        if phase in {"discussion", "collaboration"}:
            if difficulty != DifficultyHint.HARD and not force_hard:
                return self._flash_selection("phase-collaboration")
            if has_history and round_index > 1:
                return self._flash_selection("phase-collaboration-history")
            return self._pro_selection("phase-collaboration-hard")

        if phase == "plan":
            if difficulty == DifficultyHint.HARD or (difficulty == DifficultyHint.AUTO and force_hard and not has_history):
                return self._pro_selection("phase-plan-hard")
            return self._flash_selection("phase-plan-flash")

        if difficulty == DifficultyHint.HARD or (difficulty == DifficultyHint.AUTO and force_hard):
            return self._pro_selection("hard-route")
        if round_index > 1 and has_history:
            return self._flash_selection("history-flash")
        return self._flash_selection("flash-route")

    def _pro_selection(self, route_reason: str) -> ModelSelection:
        return ModelSelection(
            model=self.settings.manager_hard_model,
            thinking_enabled=True,
            reasoning_effort="high",
            route_reason=route_reason,
        )

    def _flash_selection(self, route_reason: str) -> ModelSelection:
        return ModelSelection(
            model=self.settings.manager_regular_model,
            thinking_enabled=False,
            reasoning_effort="medium",
            route_reason=route_reason,
        )
