# 架构说明

## 1. 核心目标

这个后端骨架围绕“在线二进制漏洞审计平台”搭建，优先实现以下能力：

- 中央 `ManagerAgent` 战略编排
- 多个 `Sub-Agent` 并行执行
- 子代理上下文隔离
- LLM 行为纠偏
- DeepSeek 模型分流

## 2. 模块拆分

### ManagerAgent

职责：

- 接收审计请求
- 生成核心笔记
- 规划子任务角色
- 路由模型
- 并行调度子代理
- 汇总最终报告

### Sub-Agent

每个子代理具有：

- 独立上下文窗口
- 独立笔记副本
- 独立行为观察器
- 独立工具证据采样流程
- 独立会话级协作邮箱视图

当前预置角色：

- `triage`
- `static-analysis`
- `dynamic-analysis`
- `exploitability-review`
- `exploit-strategy`

### BinaryToolbox

工具分层：

- 基础元数据：`file`、`sha256sum`
- ELF 结构：`readelf -h/-SW/-Ws/-l/-d`
- 安全属性：`checksec`
- 动态调试：`gdb`
- 覆盖探测：`AFL++`
- 静态恢复：`angr`、`IDA`
- 逆向证据：`rizin/radare2`

说明：

- `ida_batch` 优先复用 `/home/tankuku/rootfs_elf/ida_worker.py`
- 若外部导出失败，再回退到内置 headless IDA 脚本
- `rizin_overview` 现在优先调用真实 `rizin/radare2` 工具链：
  - `rabin2/rz-bin` 负责导入表、动态依赖与基础元数据
  - `radare2/rizin` 负责 `axt` 调用点交叉引用
  - 本地开发环境优先复用项目内 `.vendor/radare2` 的用户态安装

## 3. 观察者模式

### ToolLoopObserver

输入事件：`tool_invocation`

行为：

- 追踪同一命令的连续调用次数
- 达到阈值后，注入“停止重复命令、总结失败原因、切换路径”的系统干预

### NoteRecallObserver

输入事件：`note_retrieval`

行为：

- 追踪同一笔记被反复检索的次数
- 达到阈值后，强制将其标记为 `invalidated`
- 同时注入“重新验证假设”的系统干预

### ContextWindowObserver

输入事件：`reasoning_round`

行为：

- 推理轮次超过阈值后，清空大部分消息历史
- 仅重新注入核心笔记

## 4. DeepSeek 路由策略

按你给出的要求，当前路由策略是：

- 常规题：`deepseek-v4-flash`
- 困难题 / 动态分析 / 利用链策略：`deepseek-v4-pro`

说明：

- 我按 2026-05-03 查阅 DeepSeek 官方文档后，代码中使用的是官方文档里的 `deepseek-v4-flash` 与 `deepseek-v4-pro`
- 代码默认不把 API Key 写入仓库，只从环境变量读取

## 5. Docker 隔离策略

`DockerSubAgentRuntime` 的执行流程：

1. Manager 将任务序列化到 `data/runtime/<session>/<task>/payload.json`
2. Manager 为整场会话准备共享协调目录：`data/runtime/<session>/coordination`
3. 启动独立容器执行 `python -m workers.agent_worker`
4. 子代理输出 `result.json`
5. Manager 回收结果并汇总

当前隔离策略：

- 默认 `SUBAGENT_DOCKER_NETWORK_MODE=auto`
  - 已配置远端 `DeepSeek` Key 时自动切到 `bridge`
  - 未配置远端模型、走本地回退时自动切到 `none`
- 每个子代理独立进程/容器
- 只挂载工作区和运行时目录
- 为每个容器额外挂载共享协调目录 `/coordination`
- 通过 `--cidfile` 回写真实容器 ID，便于会话侧追踪“哪个子代理跑在哪个容器里”

## 6. 子代理通信

当前已实现“会话级共享信箱”机制：

- 每个子代理在以下阶段会主动广播阶段性摘要：
  - `plan`
  - `evidence`
  - `summary`
- 广播内容通过 `data/runtime/<session>/coordination/*.json` 在子代理之间共享
- 接收方会将同伴消息转为普通笔记，后续与核心笔记一起进入推理
- 这保证了：
  - 容器隔离仍然成立
  - 上下文窗口彼此独立
  - 但阶段性结论可以互相交换，而不是完全信息孤岛

相关事件：

- `agent_message_sent`
- `agent_message_received`

## 7. 持久化

### 审计会话

- 存放位置：`data/audits/*.json`

### 上传样本元数据

- 存放位置：`data/artifacts/*.json`

### 开发进度

- 存放位置：`docs/PROGRESS.md`

## 8. 实时与导出

### WebSocket 事件流

- 路径：`/api/v1/ws/audits`
- 连接后先返回：
  - `connected`
  - `tool_inventory`
  - 命中会话时附带 `session_snapshot`
- 运行期持续推送：
  - `audit_event`
  - `session_snapshot`
  - 其中 `audit_event` 现已覆盖子代理协作消息事件

### 报告导出

- 路径：`GET /api/v1/audits/{session_id}/report`
- 支持：
  - `format=markdown`
  - `format=json`
- `markdown` 导出 Manager 报告正文
- `json` 导出会话元信息、核心笔记、子代理摘要、工具证据与最终报告

## 9. 下一阶段建议

下一阶段建议优先做这四项：

1. 继续扩展真实逆向/利用工具链，如 `pwndbg`, `gef`, `ROPgadget`
2. 将审计事件做成 WebSocket 流，便于前端实时展示
3. 引入任务队列与多节点调度器，做真正的分布式 worker 池
4. 加入样本权限隔离、租户级配额与审计日志
