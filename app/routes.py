from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, Response, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, PlainTextResponse

from app.manager import LLMNotReadyError, ManagerAgentService
from app.models import (
    ArtifactRecord,
    AuditRequest,
    AuditSession,
    DeepSeekCheckRequest,
    DeepSeekCheckResult,
    DeepSeekSettingsUpdate,
    DeepSeekSettingsView,
    KnowledgeEntry,
    ReportExportFormat,
    ToolToggleUpdate,
    ToolCapability,
)

router = APIRouter()


def get_manager(request: Request) -> ManagerAgentService:
    return request.app.state.manager


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/runtime")
async def runtime_profile(
    manager: ManagerAgentService = Depends(get_manager),
) -> dict[str, object]:
    return manager.runtime_profile()


@router.get("/settings/deepseek", response_model=DeepSeekSettingsView)
async def deepseek_settings(
    manager: ManagerAgentService = Depends(get_manager),
) -> DeepSeekSettingsView:
    return manager.deepseek_settings_view()


@router.put("/settings/deepseek", response_model=DeepSeekSettingsView)
async def update_deepseek_settings(
    payload: DeepSeekSettingsUpdate,
    manager: ManagerAgentService = Depends(get_manager),
) -> DeepSeekSettingsView:
    return manager.update_deepseek_api_key(payload.api_key)


@router.post("/settings/deepseek/check", response_model=DeepSeekCheckResult)
async def check_deepseek_settings(
    payload: DeepSeekCheckRequest,
    manager: ManagerAgentService = Depends(get_manager),
) -> DeepSeekCheckResult:
    return await manager.check_deepseek_api(payload.api_key)


@router.post("/artifacts", response_model=ArtifactRecord)
async def upload_artifact(
    file: UploadFile = File(...),
    manager: ManagerAgentService = Depends(get_manager),
) -> ArtifactRecord:
    return await manager.store_artifact(file)


@router.post("/audits", response_model=AuditSession)
async def create_audit(
    request: AuditRequest,
    manager: ManagerAgentService = Depends(get_manager),
) -> AuditSession:
    try:
        return await manager.create_session(request)
    except LLMNotReadyError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/audits", response_model=list[AuditSession])
async def list_audits(
    compact: bool = Query(default=False),
    manager: ManagerAgentService = Depends(get_manager),
) -> list[AuditSession]:
    return manager.list_sessions(compact=compact)


@router.get("/audits/{session_id}", response_model=AuditSession)
async def get_audit(
    session_id: str,
    manager: ManagerAgentService = Depends(get_manager),
) -> AuditSession:
    try:
        return manager.get_session(session_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Session not found") from exc


@router.delete("/audits/{session_id}", status_code=204)
async def delete_audit(
    session_id: str,
    manager: ManagerAgentService = Depends(get_manager),
) -> Response:
    await manager.delete_session(session_id)
    return Response(status_code=204)


@router.get("/audits/{session_id}/report")
async def export_audit_report(
    session_id: str,
    format: ReportExportFormat = Query(default=ReportExportFormat.MARKDOWN),
    download: bool = Query(default=False),
    manager: ManagerAgentService = Depends(get_manager),
):
    try:
        exported = manager.build_report_export(session_id)
        filename = manager.report_filename(session_id, format)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Session not found") from exc

    headers = {}
    if download:
        headers["Content-Disposition"] = f'attachment; filename="{filename}"'

    if format == ReportExportFormat.JSON:
        return JSONResponse(exported.model_dump(mode="json"), headers=headers)

    return PlainTextResponse(
        exported.report_markdown,
        media_type="text/markdown; charset=utf-8",
        headers=headers,
    )


@router.get("/tools", response_model=list[ToolCapability])
async def list_tools(
    manager: ManagerAgentService = Depends(get_manager),
) -> list[ToolCapability]:
    return manager.list_tool_capabilities()


@router.put("/tools/{tool_id}", response_model=ToolCapability)
async def update_tool(
    tool_id: str,
    payload: ToolToggleUpdate,
    manager: ManagerAgentService = Depends(get_manager),
) -> ToolCapability:
    try:
        return manager.update_tool_enabled(tool_id, payload.enabled)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Tool not found") from exc


@router.get("/knowledge", response_model=list[KnowledgeEntry])
async def list_knowledge(
    manager: ManagerAgentService = Depends(get_manager),
) -> list[KnowledgeEntry]:
    return manager.list_knowledge_entries()


@router.delete("/knowledge/{entry_id}", status_code=204)
async def delete_knowledge_entry(
    entry_id: str,
    manager: ManagerAgentService = Depends(get_manager),
) -> Response:
    try:
        manager.delete_knowledge_entry(entry_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Knowledge entry not found") from exc
    return Response(status_code=204)


@router.websocket("/ws/audits")
async def audit_stream(websocket: WebSocket) -> None:
    await websocket.accept()
    session_id = websocket.query_params.get("session_id")
    manager: ManagerAgentService = websocket.app.state.manager
    broker = websocket.app.state.broker
    subscription = await broker.subscribe(session_id)

    try:
        await websocket.send_json({"type": "connected", "session_id": session_id})
        await websocket.send_json(
            {
                "type": "tool_inventory",
                "tool_capabilities": [
                    item.model_dump(mode="json") for item in manager.list_tool_capabilities()
                ],
            }
        )
        if session_id:
            try:
                session = manager.get_session(session_id)
            except FileNotFoundError:
                session = None
            if session is not None:
                await websocket.send_json(
                    {
                        "type": "session_snapshot",
                        "session_id": session.id,
                        "session": session.model_dump(mode="json"),
                    }
                )

        while True:
            message = await subscription.recv()
            await websocket.send_json(message)
    except WebSocketDisconnect:
        pass
    finally:
        await subscription.close()
