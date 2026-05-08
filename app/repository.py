from __future__ import annotations

import json
from pathlib import Path

from app.config import Settings
from app.models import ArtifactRecord, AuditSession


class JsonRepository:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _write_model(self, path: Path, model: object) -> None:
        if hasattr(model, "model_dump"):
            payload = model.model_dump(mode="json")
        else:
            payload = model
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _artifact_path(self, artifact_id: str) -> Path:
        return self.settings.artifact_meta_dir / f"{artifact_id}.json"

    def _session_path(self, session_id: str) -> Path:
        return self.settings.audit_dir / f"{session_id}.json"

    def save_artifact(self, artifact: ArtifactRecord) -> None:
        self._write_model(self._artifact_path(artifact.id), artifact)

    def load_artifact(self, artifact_id: str) -> ArtifactRecord:
        path = self._artifact_path(artifact_id)
        data = json.loads(path.read_text(encoding="utf-8"))
        return ArtifactRecord.model_validate(data)

    def delete_artifact(self, artifact_id: str) -> None:
        self._artifact_path(artifact_id).unlink(missing_ok=True)

    def save_session(self, session: AuditSession) -> None:
        session.touch()
        self._write_model(self._session_path(session.id), session)

    def load_session(self, session_id: str) -> AuditSession:
        path = self._session_path(session_id)
        data = json.loads(path.read_text(encoding="utf-8"))
        return AuditSession.model_validate(data)

    def delete_session(self, session_id: str) -> None:
        self._session_path(session_id).unlink(missing_ok=True)

    def list_sessions(self, limit: int | None = 20) -> list[AuditSession]:
        sessions: list[AuditSession] = []
        paths = sorted(self.settings.audit_dir.glob("*.json"), reverse=True)
        if limit is not None:
            paths = paths[:limit]
        for path in paths:
            data = json.loads(path.read_text(encoding="utf-8"))
            sessions.append(AuditSession.model_validate(data))
        return sessions

    def load_hidden_knowledge_entry_ids(self) -> set[str]:
        path = self.settings.knowledge_deleted_path
        if not path.exists():
            return set()
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            return set()
        return {str(item) for item in data if str(item).strip()}

    def save_hidden_knowledge_entry_ids(self, entry_ids: set[str]) -> None:
        path = self.settings.knowledge_deleted_path
        path.write_text(
            json.dumps(sorted(entry_ids), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
