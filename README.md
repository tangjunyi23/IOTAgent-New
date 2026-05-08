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

如果已经按仓库脚本部署到服务器，也可以直接使用仓库内脚本做启停：

```bash
./scripts/start.sh
./scripts/stop.sh
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

`start.sh` / `stop.sh` 实际上是对 `scripts/manage.sh start|stop` 的简化封装，适合部署后快速启停；如果需要查看日志、更新代码、进入容器，继续使用 `scripts/manage.sh`。

## 前端系统设置热修改

服务启动后，可以直接在前端“系统设置”页面修改大部分运行配置，保存后会立即写回当前运行态并落盘到 `.env`。

当前可在前端热修改的内容包括：

- `DeepSeek API Key`
- `DeepSeek Base URL`
- 常规模型与高难模型
- 上传目录、审计目录、样本元数据目录、运行时目录、技能数据目录
- Docker 子代理开关、镜像名、网络模式
- 最大并行子代理数、工具超时、LLM 超时、工具输出上限
- 循环干预阈值、笔记召回阈值、上下文重置阈值、协作轮数与协作超时
- `IDA` / `rootfs_elf` 等外部工具路径

说明：

- 保存后会立即影响“新的上传、新建任务和后续子代理调度”。
- 已经创建的历史会话仍按原始落盘路径读取，不会回写旧数据。
- 前端保存的配置会同步写入 `.env`，因此服务重启后仍会保留。
- 该页面可以修改 `API Key`，部署到公网或公司网络时应配合访问控制，不要裸露给未授权用户。

### 推荐修改项

部署到新服务器后，通常至少需要在“系统设置”里确认或修改以下字段：

- `DeepSeek API Key`
- `DeepSeek Base URL`
- `host_workspace_dir`
- 上传/审计/运行时相关目录
- `enable_docker_runtime`
- `subagent_docker_image`
- `subagent_docker_network_mode`
- `IDA_HEADLESS_PATH`、`HOST_IDA_INSTALL_DIR`、`HOST_IDA_USER_DIR`
- `ROOTFS_ELF_TOOL_DIR`

### 服务器路径填写规则

如果服务直接运行在宿主机上，前端里填写真实服务器路径即可，例如：

```text
upload_dir=/srv/iot-agent-new/data/uploads
audit_dir=/srv/iot-agent-new/data/audits
artifact_meta_dir=/srv/iot-agent-new/data/artifacts
runtime_dir=/srv/iot-agent-new/data/runtime
skill_data_dir=/srv/iot-agent-new/data/skills
knowledge_deleted_path=/srv/iot-agent-new/data/knowledge/deleted_entries.json
host_workspace_dir=/srv/iot-agent-new
```

如果使用当前仓库自带的 `docker-compose.prod.yml` 部署，`manager` 服务运行在容器内，而项目宿主目录挂载到容器内的 `/workspace`。这时建议这样填写：

```text
upload_dir=/workspace/data/uploads
audit_dir=/workspace/data/audits
artifact_meta_dir=/workspace/data/artifacts
runtime_dir=/workspace/data/runtime
skill_data_dir=/workspace/data/skills
knowledge_deleted_path=/workspace/data/knowledge/deleted_entries.json
host_workspace_dir=/srv/iot-agent-new
```

注意：

- `upload_dir`、`audit_dir`、`artifact_meta_dir`、`runtime_dir`、`skill_data_dir`、`knowledge_deleted_path`：
  在 Docker 部署下应填写“容器内路径”，通常是 `/workspace/...`
- `host_workspace_dir`：
  这里必须填写“宿主机上的项目绝对路径”，例如 `/srv/iot-agent-new`

### 外部工具路径说明

以下字段依赖服务器上真实安装情况，不需要时可以留空：

- `IDA_HEADLESS_PATH`
- `HOST_IDA_INSTALL_DIR`
- `HOST_IDA_USER_DIR`
- `ROOTFS_ELF_TOOL_DIR`

如果公司服务器没有安装 `IDA` 或 `rootfs_elf`，建议先留空，平台仍可正常运行，只是对应工具能力会不可用。

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
