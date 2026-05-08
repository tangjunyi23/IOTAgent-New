# 在线二进制漏洞审计平台后端

这是一个面向二进制漏洞审计场景的全栈 MVP，目前以后端编排为核心，并附带一个可直接交互的浏览器前端。

- `Manager Agent + Sub-Agent` 编排
- `Docker` 隔离子代理运行时
- `观察者模式` 的行为纠偏机制
- `DeepSeek` 模型路由与会话/进度持久化

## 已实现能力

- `FastAPI` 接口，支持上传二进制样本、创建审计任务、查询任务状态
- 浏览器单页控制台，支持上传样本、创建审计会话、查看实时事件、导出报告与阅读开发进度
- 中央 `ManagerAgent` 负责拆分子任务并并行调度
- 子代理支持两种运行模式：
  - `InProcessSubAgentRuntime`：默认本地开发模式
  - `DockerSubAgentRuntime`：每个子代理独立容器执行
- 已接入 `checksec`、`rizin/radare2`、`gdb`、`AFL++`、`angr`、`IDA`
- 本地开发环境会优先复用项目内 `.vendor/radare2` 的用户态安装，不依赖宿主机 `apt install`
- `ida_batch` 优先复用 `/home/tankuku/rootfs_elf/ida_worker.py`，失败时回退到内置 headless IDA 导出
- 提供 WebSocket 实时事件流与工具能力清单接口
- 支持将审计结果导出为 `Markdown` 或结构化 `JSON`
- 行为纠偏观察器：
  - `ToolLoopObserver`：连续重复同一命令达到阈值后，注入干预指令
  - `NoteRecallObserver`：同一笔记反复检索达到阈值后，强制清除
  - `ContextWindowObserver`：推理轮次超限后，清空上下文并仅回注核心笔记
- `DeepSeek` 模型路由：
  - 常规任务默认走 `deepseek-v4-flash`
  - 难题、动态分析、利用性评估默认走 `deepseek-v4-pro`
- 审计会话、样本元数据、开发进度文档持久化

## 目录结构

```text
app/
  config.py
  events.py
  llm.py
  main.py
  manager.py
  models.py
  model_router.py
  observers.py
  repository.py
  routes.py
  subagent.py
  toolbox.py
frontend/
  index.html
  static/
    app.js
    styles.css
workers/
  agent_worker.py
docs/
  ARCHITECTURE.md
  PROGRESS.md
data/
  uploads/
  audits/
```

## 启动方式

1. 安装依赖：

```bash
pip install -e .[dev]
```

2. 配置环境变量：

```bash
cp .env.example .env
```

注意：

- 不要把真实 `DeepSeek API Key` 写进代码仓库。
- 本项目只读取环境变量 `DEEPSEEK_API_KEY`。

3. 启动服务：

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 10000
```

4. 打开前端：

浏览器访问：

```text
http://127.0.0.1:10000/
```

如果要从同一局域网内的另一台机器访问，请改用当前主机 IP，例如：

```text
http://<host-ip>:10000/
```

5. 访问接口：

- `POST /api/v1/artifacts`
- `POST /api/v1/audits`
- `GET /api/v1/audits`
- `GET /api/v1/audits/{session_id}`
- `GET /api/v1/audits/{session_id}/report?format=markdown|json`
- `GET /api/v1/progress`
- `GET /api/v1/tools`
- `WS /api/v1/ws/audits`

## Docker 子代理

构建子代理镜像：

```bash
docker build -f Dockerfile.subagent -t binary-audit-subagent:latest .
```

启用 Docker 隔离：

```bash
export ENABLE_DOCKER_RUNTIME=true
export HOST_WORKSPACE_DIR=$(pwd)
```

说明：

- `HOST_WORKSPACE_DIR` 必须是宿主机上项目绝对路径。
- 子代理容器通过挂载该目录读取上传样本与运行时代码。

## 一键部署到服务器

如果服务器已经装好 `git`、`docker`、`docker compose`，直接执行：

```bash
curl -fsSL https://raw.githubusercontent.com/tangjunyi23/IOTAgent-New/main/scripts/deploy.sh \
  | DEEPSEEK_API_KEY=your_key_here bash
```

如果是全新 Linux 服务器，希望脚本自动安装依赖后再部署，执行：

```bash
curl -fsSL https://raw.githubusercontent.com/tangjunyi23/IOTAgent-New/main/scripts/bootstrap-linux.sh \
  | DEEPSEEK_API_KEY=your_key_here bash
```

常用可选变量：

```bash
curl -fsSL https://raw.githubusercontent.com/tangjunyi23/IOTAgent-New/main/scripts/deploy.sh \
  | APP_DIR=/srv/iot-agent-new \
    APP_PORT=10000 \
    ENABLE_DOCKER_RUNTIME=true \
    DEEPSEEK_API_KEY=your_key_here \
    bash
```

说明：

- 脚本默认从 `main` 分支拉取 `https://github.com/tangjunyi23/IOTAgent-New.git`
- 默认部署目录是 `/srv/iot-agent-new`
- 默认会启用 `DockerSubAgentRuntime`，并自动构建 `binary-audit-subagent:latest`
- 生产编排文件为 `docker-compose.prod.yml`
- 首次执行会用 `.env.example` 生成 `.env`，并把 `HOST_WORKSPACE_DIR` 固定为部署目录
- `deploy.sh` 会在缺少依赖时自动安装 `git`、`curl` 和 `docker`
- 日常运维可以直接使用 `scripts/manage.sh`
- 部署后也可以直接用 `scripts/start.sh` 和 `scripts/stop.sh` 做快速启停

部署后常用命令：

```bash
cd /srv/iot-agent-new
./scripts/start.sh
./scripts/stop.sh
./scripts/manage.sh status
./scripts/manage.sh logs
./scripts/manage.sh update
./scripts/manage.sh restart
```

## 当前审计能力边界

当前版本聚焦“可运行的在线审计骨架”，不是完整漏洞利用平台。现在已具备：

- ELF/通用二进制基础信息采集
- `file` / `sha256sum` / `readelf` / `strings` / `checksec` / `gdb` / `AFL++` / `angr` / `IDA` 证据采样
- LLM 驱动的子代理计划、结论生成与 Manager 汇总报告
- 报告导出、实时事件流与工具能力探测

下一步适合接入：

- `pwndbg` 等尚未完成的外部工具
- 更细粒度的任务队列和节点调度
- 更结构化的漏洞发现归档与报告模板
- 样本沙箱与多租户权限控制
