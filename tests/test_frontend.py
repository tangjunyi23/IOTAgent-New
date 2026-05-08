from fastapi.testclient import TestClient

from app.main import app


def test_frontend_index_served():
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert "思而听二进制漏洞审计平台" in response.text
        assert "首页" in response.text
        assert "审计项目" in response.text
        assert "审计项目任务管理" in response.text
        assert "报告生成" in response.text
        assert "知识库" in response.text
        assert "系统设置" in response.text
        assert "新建审计任务" in response.text
        assert "上传任务文件并创建审计" in response.text
        assert "保存 API Key" in response.text
        assert "保存系统设置" in response.text
        assert "路径存储、模型配置与运行参数" in response.text
        assert "批量删除历史任务" in response.text
        assert "批量删除任务" in response.text
        assert "批量删除历史" in response.text
        assert 'id="app-dialog-modal"' in response.text
        assert "开发进度文档" not in response.text
        assert "分析师笔记" not in response.text
        assert "/bin/ls 或项目内样本路径" not in response.text
        assert "模型后端" not in response.text
        assert "模型路由" not in response.text
        assert "清除当前项目" in response.text
        assert "在线二进制漏洞审计平台" not in response.text
        assert 'value="样本初始审计"' not in response.text
        assert "实时状态" not in response.text
        assert "当前通过自动轮询同步项目状态与报告变化。" not in response.text


def test_frontend_static_js_served():
    with TestClient(app) as client:
        response = client.get("/static/app.js")
        assert response.status_code == 200
        assert "const state" in response.text
        assert "function rememberExpandedPanels(root)" in response.text
        assert "本地回退模式" not in response.text
        assert "loadDemoPayload" not in response.text
        assert "target-path" not in response.text
        assert "analyst-notes" not in response.text
        assert "handleDeleteSession" in response.text
        assert "handleCheckApi" in response.text
        assert "handleSaveSystemSettings" in response.text
        assert "handleToggleTool" in response.text
        assert "renderActivityStreamIncremental" in response.text
        assert "buildCoordinationDescriptor" in response.text
        assert "stream-subcopy" in response.text
        assert "confirmAction(" in response.text
        assert "renderInlineStructuredText" in response.text
        assert "code-block-shell" in response.text
        assert "code-line-text" in response.text
        assert '"Dynamic Analysis"' in response.text
        assert '"Static Analysis"' in response.text
        assert '"Exploitability Review"' in response.text
        assert "ensureAuditRuntimeReady" in response.text
        assert "settings/system" in response.text
        assert 'document.addEventListener("toggle", (event) => {' in response.text
        assert "审计后端未就绪" in response.text
        assert "window.alert" not in response.text
        assert "window.confirm" not in response.text


def test_tool_inventory_endpoint():
    with TestClient(app) as client:
        response = client.get("/api/v1/tools")
        assert response.status_code == 200
        data = response.json()
        tool_ids = {item["tool_id"] for item in data}
        assert {"checksec", "gdb_batch", "gdb_poc", "ida_batch", "angr_cfg", "function_disasm", "function_xrefs"} <= tool_ids
        afl_tool = next(item for item in data if item["tool_id"] == "afl_showmap_probe")
        assert afl_tool["enabled"] is False


def test_runtime_endpoint():
    with TestClient(app) as client:
        response = client.get("/api/v1/runtime")
        assert response.status_code == 200
        data = response.json()
        assert {
            "llm_backend",
            "llm_provider",
            "llm_configured",
            "regular_model",
            "hard_model",
            "manager_round_policy",
            "subagent_model_policy",
            "token_tracking",
            "disabled_tool_ids",
        } <= data.keys()


def test_audit_websocket_connects_and_sends_inventory():
    with TestClient(app) as client:
        with client.websocket_connect("/api/v1/ws/audits") as websocket:
            connected = websocket.receive_json()
            inventory = websocket.receive_json()

        assert connected["type"] == "connected"
        assert inventory["type"] == "tool_inventory"
        assert any(item["tool_id"] == "checksec" for item in inventory["tool_capabilities"])
