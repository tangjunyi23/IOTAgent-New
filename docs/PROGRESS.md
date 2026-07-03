# 项目开发进度

## 2026-07-03

### 增量进展（LLM 提供商泛化为 OpenAI 兼容 / rootfs_elf 导出器替换 / Manager 与 GDB 强化）

本轮把“DeepSeek 专用”这条贯穿配置、后端、路由、前端的链路泛化为“OpenAI 兼容”，并把 CTF-pwn 技能包的 IDA 导出器换成 vendored `rootfs_elf` 包，同时继续强化 Manager 续轮收敛与 GDB 溢出探测。三块改动运行时耦合较紧（`available_tools` 参数同时服务于 LLM 泛化与提示词推进；`toolbox.py` 同文件内含导出器选择与 GDB 探测两个主题），因此合并为单次 feat 提交 `2761cd5` 落地，并已推送至 `origin/main`。

#### LLM 提供商泛化（DeepSeek → OpenAI 兼容）

- 配置层：
  - `app/config.py` 把 `deepseek_api_key` / `deepseek_base_url` 重命名为 `llm_api_key` / `llm_base_url`，并保留向后兼容的 property（旧代码读 `settings.deepseek_api_key` 仍可用）
  - 新增 `migrate_legacy_llm_env`（`@model_validator(mode="before")`）把旧 `DEEPSEEK_API_KEY` / `DEEPSEEK_BASE_URL` 环境变量自动迁移到新 `llm_*` 键
  - `manager_regular_model` / `manager_hard_model` 默认值从写死的 `deepseek-v4-flash` / `deepseek-v4-pro` 改为 `None`，由用户自行填写模型名
  - `pwn_skill_zip_path` 不存在时回退到 `~/pwnskill.zip` 或 `~/ctf-pwn-skill-with-kb-2026-04-30.zip`
- 后端 LLM：
  - `DeepSeekLLMBackend` → `OpenAICompatibleLLMBackend`、`MissingDeepSeekLLMBackend` → `MissingLLMBackend`（模块底部保留旧别名，旧 import 不破）
  - 客户端改用 `settings.llm_api_key` / `settings.llm_base_url` 构造
  - `_complete` 改为按候选 kwarg 变体逐个尝试（`reasoning_effort+thinking` → `reasoning_effort` → `thinking` → 纯净），通过新 `_is_feature_compatibility_error` 吞掉 `reasoning_effort` / `thinking` / `unsupported` / `unknown parameter` 等特性兼容错误，非兼容错误立即上抛
  - 新增 `list_openai_compatible_models()` 调用 `client.models.list()` 返回模型清单
  - `probe_deepseek_connection` → `probe_openai_compatible_connection`，接受显式 `base_url` / `model`，先试 thinking-disabled 再试纯净 ping，并正确 `await` 异步 `client.close()`
- 数据模型（`app/models.py`）：
  - `DeepSeekSettingsView/Update/CheckRequest/CheckResult` → `LLMProvider*` 系列视图
  - 新增 `LLMModelInfo` / `LLMProviderModelsResult`（模型列表端点用）
  - 新增 `ToolHealthCheckResult`（工具健康检查用）
  - `AuditRequest` / `AuditReportExport` 新增 `desired_outcome` / `audit_mode`
  - `SubAgentPayload` 新增 `available_tool_ids`
  - `SystemSettingsView` 新增 `llm_provider` / `llm_configured` / `llm_key_preview` / `llm_status` / `llm_base_url` / `manager_regular_model` / `manager_hard_model`，旧 `deepseek_*` 字段保留为 `| None` 兼容
  - `ModelSelection.model` 类型放宽为 `str | None`（模型可选后允许空选择）
- 路由（`app/routes.py`）：
  - `GET/PUT /settings/deepseek` → `/settings/llm`（保留旧路径作别名）
  - `POST /settings/deepseek/check` → `/settings/llm/check`（保留别名）
  - 新增 `POST /settings/llm/models` 返回 `LLMProviderModelsResult`
  - 新增 `POST /tool-health-check` 返回 `list[ToolHealthCheckResult]`
- Manager（`app/manager.py`）：
  - `deepseek_settings_view` → `llm_settings_view`、`update_deepseek_api_key` → `update_llm_settings(api_key, base_url)`、`check_deepseek_api` → `check_llm_api(api_key, base_url, model)`
  - 新增 `list_llm_models()` / `run_tool_health_checks()`
  - 运行时状态新增 `missing_regular_model` / `missing_hard_model` 守卫与 `_provider_label()`（base_url 含 deepseek 返回 `deepseek`，否则 `openai-compatible`）
  - `runtime_profile` 聚合最近 20 场会话的 token 用量，上报 `cached_tokens` 与 `cache_hit_ratio`
  - `build_report_export` 纳入 `desired_outcome` / `audit_mode`
  - 持久化 `llm_*` 时同步镜像到旧 `DEEPSEEK_*` 环境变量，热更新不丢旧调用方
- 子代理（`app/subagent.py`）：
  - Docker 容器环境变量改为 `LLM_API_KEY` / `LLM_BASE_URL`，同时保留旧 `DEEPSEEK_*` 镜像
  - `_docker_network_mode` 自动选择改以 `settings.llm_api_key` 为依据
- 前端：
  - `frontend/index.html` 表单 `deepseek-settings-form` → `llm-settings-form`，标签改 “OpenAI-Compatible API Key”，新增 Base URL 字段、`获取模型列表` / `检测工具环境` 按钮与对应状态容器
  - 系统设置模态框 “DeepSeek 模型” → “OpenAI-Compatible 模型”，`deepseek_base_url` → `llm_base_url`，模型名占位符改为 “用户自行填写模型名”
  - 新增任务表单字段 `#task-desired-outcome`（六级成果目标）与 `#task-audit-mode`
  - `app.js` 全面改名 `deepseekSettings` → `llmSettings`、`loadDeepSeekSettings` → `loadLlmSettings`；新增模型列表卡片（带“填入常规模型 / 填入高难模型”按钮）、工具健康检查卡片、子代理归档面板；视图切换用 `Symbol` token 防止 stale 回调污染 DOM，`setTimeout(…,30)` 改为 `requestAnimationFrame`
  - `styles.css` 补 `scrollbar-gutter: stable` 与 `.main-shell` / `.view` 的 `width: 100%`
  - 静态资源版本号刷新为 `?v=20260526e`

#### CTF-pwn 技能：换用 vendored `rootfs_elf` 导出器

- 新增 vendored `data/skills/ctf-pwn/scripts/rootfs_elf/` 包（11 个文件）：
  - `ida_worker.py`（单 ELF 导出，`rootfs_elf_single.py` 的目标）
  - `analyzer.py` / `cli.py`（批量，`rootfs_elf_batch.py` 的目标）
  - `scanner.py`（rootfs 树扫描与 ELF 分类）、`checksec.py`、`config.py`（`ensure_ida_env` / IDA 路径解析）、`utils.py`、`model_types.py`、`__init__.py` / `__main__.py`
  - 产物布局：`source.c` / `function_index.jsonl` / `decompile/*.c` / `strings.txt` / `imports.txt` / `exports.txt` / `data_symbols.txt` / 可选 `memory/`；批量另增 `summary.json` / `indexes/*` / `by_elf/<elf_id>/...`
- 新增两个 shim：`rootfs_elf_single.py` / `rootfs_elf_batch.py`
- 删除旧 `scripts/export_headless_pseudocode.py`（244 行，被新包取代）
- `SKILL.md` 与 `references/headless_ida_export.md` 整体重写：
  - 偏好反编译路径改为 vendored `rootfs_elf_single.py` / `rootfs_elf_batch.py`
  - Ghidra 从“禁止”改为“IDA+调试器工作流失败后的最后兜底”
  - 新增 IDA 自发现规则（`IDADIR` → `~/ida-pro-*` → `/opt/idapro*` → `--ida-dir`）
- `.source.json` 把 `zip_path` 指向 `~/pwnskill.zip`，更新 `size` / `mtime_ns`
- `app/pwn_skill.py` 新增 `rootfs_elf_single_script_path()` / `rootfs_elf_batch_script_path()` / `ida_reference_excerpt()` / `methodology_excerpt()`
- `app/toolbox.py` 的 `_run_ida_batch` 按导出器脚本名分支：`rootfs_elf_single.py` 不传 `--skip-memory` / `--no-decompile-funcs` / `--log-path`；`_resolve_rootfs_elf_exporter_script` 优先选 `rootfs_elf_single.py`，其次 `ida_worker.py`
- 新增 4 份 methodology 写作：`attachment_30`（有符号索引越界 + ret2libc）、`borrowstack`（i386 栈溢出 + 连续 GOT 泄露）、`ring_factory`（5 字节 `%7$p` canary 泄露 + UAF + 栈破坏 ret2libc）、`deepvoid`（堆溢出 unsafe-unlink → `strtol@got`→`system`），并补 `methodologies/index.md` 表格与 `patterns.md` 一条 i386 连续 GOT 指纹经验
- `references/methodology_generation.md` 模板把 “ida-no-mcp Pseudocode” 改为 “IDA Pseudocode”

#### Manager / GDB 强化与测试

- 工具可用性门控（`app/toolbox.py`）：
  - 新增 `available_tool_ids()`（同时 `available` 且 `enabled`）与 `run_health_checks()`
  - `plan_follow_up` 与角色流水线在 `is_tool_enabled` 之外，再校验 `_build_capability(tool_id).available`，才调度 `function_disasm` / `gdb_poc` / `function_xrefs`
  - 新增 `_check_capability_health()` / `_tool_probe_commands()`：python/ida 模式直接判 ok，可执行模式用 `--version` / `-v` / `-V` / `--help` 探测，`asyncio.to_thread` 执行并带超时
  - `ROLE_PIPELINES` 给每个角色补 `function_disasm`
- GDB 溢出探测大幅扩展（`_run_gdb_overflow_probe` / `_parse_gdb_overflow_output`）：
  - 新增 `breakpoint pending on` / `print thread-events off` / `handle SIGPIPE`，捕获 pre/post-call 寄存器、frame（`x/24gx $rbp-0x80`）与 buffer（`x/64bx` / `x/96bx`）转储，`ni` 单步过调用，再 `continue` 到信号
  - 新增 `_overflow_probe_registers(call_target)` 把 read/fgets/gets/recv/recvfrom 映射到 (buffer_reg, length_reg)
  - 输出按段落标记解析：`===PRECALL===` / `===FRAME_PRE===` / `===BUF_PRE===` / `===CALL_STEP===` / `===POSTCALL===` / `===FRAME_POST===` / `===BUF_POST===` / `===CONTINUE===` / `===POSTSIGNAL===`
  - 阶段分类新增 `canary-overwrite`（`stack smashing detected` / `__stack_chk_fail`），`stack-overwrite` 同时参考 `post_frame_offsets` / `buffer_offsets`
  - `_build_overflow_verdict` / `_build_gdb_poc_script` 同步 canary 分支
  - 新增 `_collect_pattern_offsets(pattern, lines)` 去重提取所有 cyclic-pattern 偏移
- Manager 续轮收敛（`app/manager.py`）：
  - `_should_expand_round` / `_decide_round_expansion` 新增硬上限轮次 3、仅阻塞且无新增完成工具时早退、round≥2 时无新增完成工具与无新增 highlights 即停
  - `_build_subagent_core_notes` 从 6 条扩到最多 12 条，追加 manager highlights（top 4）与 RCE 评估边界行（top 3）
  - 新增 `_extract_task_stage_boundary(task)` 扫描输出/笔记中的 getshell/RCE/RIP-control/stack-overwrite/info-leak/crash 行，连同跨角色阶段进度一起塞进 continuation brief
  - `_collect_manager_highlights` 在 `promoted_notes` 为空时回退到 `_extract_summary_key_points(task.output_summary)`
  - RCE 评估新增 `canary-overwrite` / `stack-overwrite` 阶段，渲染证据补 `probe_buffer_line` 与 canary/smash 注记
  - 报告移除“子代理归档”段落
- 提示词推进（`app/llm.py` / `app/subagent.py` / `app/pwn_skill.py`）：
  - LLM 协议所有方法新增 `available_tools` kwarg；`_tool_hint_for_role` 把角色提示工具与“可用且启用”的工具取交集
  - 提示词明确要求：已有崩溃证据时不得把“再次验证崩溃”当终点，必须推进到 leak / 栈覆盖 / canary 命中 / RIP 可控 / RCE / getshell；canary/PIE/Full RELRO 阻断时也要写清当前最接近的可证明阶段
  - 禁止规划“可用”以外的工具；基础工具已跑则默认禁止重规划，除非写明补的是哪个新缺口
  - `pwn_skill.py` 角色笔记补 IDA 优先 `rootfs_elf_single.py` 与 `methodology_excerpt` 摘要

### 当前验证

- `./.venv/bin/python -m pytest tests/ -q` 通过，结果：`66 passed in 35.25s`
- 已单次 feat 提交 `2761cd5`（41 文件，+3935/-557），含新增 `scripts/rootfs_elf/` 包、4 份 methodology、删除旧 `export_headless_pseudocode.py`
- 已 `git push origin main`，推送 `07973d7..2761cd5`，本地 `main` 与 `origin/main` ahead/behind = `0 0`，工作区干净

### 当前风险与遗留

- `rootfs_elf_batch.py` / `rootfs_elf_single.py` 依赖 `scripts/` 在 `sys.path` 上（`from rootfs_elf... import`），容器内调用需确认 `scripts/` 已挂载或加入路径
- 新的 `/settings/llm/*` 与旧 `/settings/deepseek/*` 别名并存，前端已切到新路径；若后续要彻底去 DeepSeek 命名，需同步移除别名与 `SystemSettingsView` 里的 `deepseek_*` 兼容字段
- thinking 参数降级靠错误关键字匹配（`unsupported` / `unknown parameter` / `invalid_request_error` 等），不同 OpenAI 兼容服务端的错误文案若不一致，可能误判为非兼容错误而上抛

## 2026-05-08

### 增量进展（Manager 续轮纠偏 / 前端静态版本刷新 / 实机可访问性复核）

- 已修正 `ManagerAgentService` 的一类无意义续轮：
  - `app/manager.py::_coerce_planned_subagents()` 不再过早把缺失的 `stage_goal` 填成默认值
  - `app/manager.py::_build_role_planned_steps()` 现仅把 **明确规划过的阶段目标/证据项** 计入硬性检查点
  - 对于 LLM 只给出角色目标与协作重点、但未显式规划深度 exploit-stage 检查点的会话，不再因为默认深审计提示而重复起第 2 轮
- 已刷新前端静态资源版本：
  - `frontend/index.html` 现改为引用 `styles.css?v=20260508a`
  - `frontend/index.html` 现改为引用 `app.js?v=20260508a`
  - 避免浏览器继续命中旧缓存，导致前端拿不到本轮折叠面板、英文角色名、Manager 驱动进度等更新
- 已复核“前端不可访问”问题并以真实 HTTP 为准：
  - 重启过程中曾短暂复现 `curl: (7) Failed to connect to 127.0.0.1:10000`
  - 重新以前台方式拉起最新 `uvicorn` 后已确认恢复
  - 当前真实监听地址是 `0.0.0.0:10000`，不是旧上下文里的 `127.0.0.1:10000`

### 当前验证

- `./.venv/bin/python -m py_compile app/*.py tests/test_llm.py tests/test_toolbox.py tests/test_manager_report.py tests/test_frontend.py tests/test_coordination.py tests/test_session_flow.py` 通过
- `node --check frontend/static/app.js` 通过
- `./.venv/bin/pytest -q tests/test_llm.py tests/test_toolbox.py tests/test_manager_report.py tests/test_frontend.py tests/test_coordination.py tests/test_session_flow.py` 通过，结果：`49 passed`
- `./.venv/bin/pytest -q` 通过，结果：`59 passed`
- 当前最新 `uvicorn` 已按最新代码运行在 `0.0.0.0:10000`，真实 HTTP 验证通过：
  - `GET http://127.0.0.1:10000/` 返回 `200`，并确认首页引用：
    - `/static/styles.css?v=20260508a`
    - `/static/app.js?v=20260508a`
  - `GET http://127.0.0.1:10000/static/app.js` 返回 `200`
  - `GET http://127.0.0.1:10000/static/styles.css` 返回 `200`
  - `GET http://127.0.0.1:10000/api/v1/runtime` 返回 `200`
    - `llm_backend=DeepSeekLLMBackend`
    - `llm_status=ready`
    - `docker_runtime=true`

## 2026-05-05

### 增量进展（LLM 就绪态修正 / 创建任务前置拦截 / 前端预检）

- 已修正 `GET /api/v1/runtime` 的 LLM 运行时返回：
  - `app/manager.py` 不再硬编码 `llm_backend=DeepSeekLLMBackend`
  - 现在会按真实后端返回 `llm_backend` / `llm_status` / `llm_configured` / `llm_error`
  - 未配置 `DEEPSEEK_API_KEY` 时会明确返回 `MissingDeepSeekLLMBackend` 与 `missing_api_key`
- 已将“LLM 未就绪”前置到任务创建入口：
  - `app/manager.py` 新增集中 `ensure_llm_ready()`
  - `POST /api/v1/audits` 在缺失 DeepSeek Key 时直接返回 `409`
  - 不再出现“前端显示已创建、后台再异步失败”的误导行为
- 已补前端创建前预检：
  - `frontend/static/app.js` 新增 `ensureAuditRuntimeReady()`
  - 上传样本前会先请求 `/api/v1/runtime`
  - 若后端未就绪，会直接提示用户跳转到“系统设置”，避免未配 Key 时产生孤儿上传文件
- 已更新静态资源版本：
  - `frontend/index.html` 现引用 `20260505e`

### 当前验证

- `./.venv/bin/python -m py_compile app/manager.py app/routes.py app/llm.py app/config.py app/subagent.py app/toolbox.py tests/test_frontend.py tests/test_session_flow.py` 通过
- `node --check frontend/static/app.js` 通过
- `./.venv/bin/pytest -q` 通过，当前结果：`53 passed`
- 当前 `10000` 端口原先无运行进程，已用最新代码重启 `uvicorn` 后做真实 HTTP 验证：
  - `GET http://127.0.0.1:10000/` 已确认输出：
    - `思而听二进制漏洞审计平台`
    - `/static/styles.css?v=20260505e`
    - `/static/app.js?v=20260505e`
  - `GET http://127.0.0.1:10000/static/app.js` 已确认包含：
    - `ensureAuditRuntimeReady`
    - `审计后端未就绪`
    - `检查环境...`
  - `GET http://127.0.0.1:10000/api/v1/runtime` 当前返回：
    - `llm_backend=DeepSeekLLMBackend`
    - `llm_provider=deepseek`
    - `llm_status=ready`
    - `llm_error=null`
    - `docker_runtime=true`
  - `GET http://127.0.0.1:10000/api/v1/settings/deepseek` 当前返回：
    - `configured=true`
    - `status=ready`

### 增量进展（完成后待命支援 / 新焦点函数补跑 / PoC 脚本前置）

- 已修正“子代理完成后就退出协作回路”的问题：
  - `app/subagent.py` 现会在首次总结广播后进入 `standby support`
  - 只要同轮其他代理还在继续发送问题/总结，已完成代理仍会继续收消息、回复协查，并可补跑额外 follow-up
  - 待命期间若新增证据或收到关键同伴上下文，会重新刷新最终 summary，再返回给 Manager 落库
- 已修正“收到新焦点函数但不再补跑 follow-up”的问题：
  - `app/toolbox.py` 的 `plan_follow_up()` 不再只按是否出现过 `command_id` 决定
  - 现在会按“该函数是否已经做过 `function_disasm` / `function_xrefs`”和“该 issue target 是否已经做过 `gdb_poc`”来决定是否继续派活
  - 静态代理在晚到协查中也可继续补跑新的函数级取证
- 已增强最终报告对 PoC 的呈现：
  - `app/manager.py` 的 `## RCE / getshell 结论` 现会显式写出已生成脚本化 PoC，而不只停留在 GDB 调试命令
  - `## 已验证 POC` 现将 `漏洞利用脚本 PoC` 代码块前置到 GDB 命中和触发命令之前
- 已增强远端 LLM 提示：
  - `app/llm.py` 现明确要求：若证据里已有 `gdb_poc.exploit_script / poc`，总结中必须说明“已产出脚本化 PoC”，不能只复述 GDB 命令

### 当前验证（本轮追加）

- `./.venv/bin/python -m py_compile app/subagent.py app/toolbox.py app/manager.py app/llm.py tests/test_coordination.py tests/test_toolbox.py tests/test_manager_report.py` 通过
- `./.venv/bin/pytest -q tests/test_coordination.py tests/test_toolbox.py tests/test_manager_report.py` 通过，结果：`24 passed`
- `./.venv/bin/pytest -q` 通过，当前结果：`56 passed`
- 当前 `10000` 端口旧 `uvicorn` 进程已停止并用最新代码重启，真实 HTTP 验证通过：
  - `GET http://127.0.0.1:10000/api/v1/runtime` 返回：
    - `llm_backend=DeepSeekLLMBackend`
    - `llm_provider=deepseek`
    - `llm_status=ready`
    - `docker_runtime=true`
  - `GET http://127.0.0.1:10000/api/v1/tools` 已确认仍返回：
    - `gdb_poc`
    - `function_disasm`
    - `function_xrefs`
  - `GET http://127.0.0.1:10000/` 已确认首页仍正常加载：
    - `思而听二进制漏洞审计平台`
    - `新建审计任务`
    - `系统设置`

### 增量进展（删除接口幂等化 / 批量删除误报修正）

- 已修正批量删除时“部分失败”的一类误报：
  - 原因是 `DELETE /api/v1/audits/{session_id}` 先 `load_session()`，若会话已被前一步删除或前端选中集滞后，后端会返回 `404 Session not found`
  - 前端会把该 `404` 计入 `failedIds`，于是弹出“批量删除部分失败”
- 现在 `app/manager.py::delete_session()` 已改为幂等删除：
  - 会话文件不存在时仍继续清理 `runtime/<session_id>` 残留
  - 并直接返回成功，不再把“已不存在”视为错误
- `app/routes.py` 已同步放宽 `DELETE /api/v1/audits/{session_id}`：
  - 删除已不存在的任务现在也返回 `204`
- 已新增回归测试：
  - `tests/test_session_flow.py::test_delete_audit_is_idempotent_for_missing_session`

## 2026-05-04

### 增量进展（任务删除 / 知识库删除 / 设置页 API Key / 视图动画）

- 已新增任务删除能力：
  - 后端新增 `DELETE /api/v1/audits/{session_id}`
  - 会真实清理会话 JSON、运行目录 `data/runtime/<session_id>`、未被其他会话引用的上传样本与元数据
  - 若目标会话仍在运行，会先取消 `Manager` 任务，再清理 Docker 子代理容器与 runtime 目录，避免“前端删掉但后台仍在跑”
- 已新增知识库历史删除能力：
  - 后端新增 `GET /api/v1/knowledge` 与 `DELETE /api/v1/knowledge/{entry_id}`
  - 知识库条目改为由后端生成稳定 `entry_id`
  - 已删除历史会写入 `data/knowledge/deleted_entries.json`，刷新后不会重新出现
- 已新增 DeepSeek 设置能力：
  - 后端新增 `GET /api/v1/settings/deepseek`
  - 后端新增 `PUT /api/v1/settings/deepseek`
  - 后端新增 `POST /api/v1/settings/deepseek/check`
  - API Key 会持久化写回项目 `.env`
  - `ManagerAgentService` 会在保存后热更新 `llm_backend` 与运行时配置，新建会话立即生效
  - API 可用性检测会真实发起一次最小 `DeepSeek` completion，请求失败时返回明确错误，不走本地回退
- 已继续前端重构与美化：
  - 平台主标题 `思而听二进制漏洞审计平台` 已上移到首页顶部主视觉区，不再放在左上角侧边栏
  - 左下角的 `实时状态 / 轮询同步中 / 当前通过自动轮询同步项目状态与报告变化。` 已删除
  - 设置页左侧改为可操作面板，支持填写 `DeepSeek API Key`、保存配置、检测当前 API 是否可用，并保留系统状态卡片
  - 审计项目、任务管理、报告页与首页快速列表已加入任务删除入口
  - 知识库卡片已加入历史删除入口
  - 所有切换页面的按钮统一接入过渡动画，切页不再生硬
- 已保持此前前端真实修复不回退：
  - `getTaskObservedToolIds`
  - `getTaskFinishedSteps(task, sessionEntries)`
  - `getSessionProgressPercent(session, sessionEntries)`
  - 运行中子代理的进度仍然同时统计已落库 evidence 与实时 `tool_result` 事件

### 当前验证

- `node --check frontend/static/app.js` 通过
- `./.venv/bin/python -m py_compile app/*.py tests/test_frontend.py tests/test_session_flow.py` 通过
- `./.venv/bin/pytest -q` 通过，当前结果：`45 passed`
- 已用本地 `uvicorn` 临时拉起最新代码并做真实 HTTP 验证：
  - `GET /api/v1/runtime` 返回：
    - `llm_backend=DeepSeekLLMBackend`
    - `llm_provider=deepseek`
    - `llm_status=ready`
    - `docker_runtime=true`
  - `GET /` 已确认输出：
    - 首页标题 `思而听二进制漏洞审计平台`
    - 设置页文案 `保存 API Key`
  - `GET /` 已确认不再包含：
    - `实时状态`
    - `当前通过自动轮询同步项目状态与报告变化。`
  - `GET /api/v1/knowledge` 可返回现有历史知识条目
  - `GET /api/v1/settings/deepseek` 可返回当前配置状态与脱敏后的 `key_preview`

### 增量进展（前端风格弹窗 / 批量删除 / 会话完成后自动清理上传样本）

- 已移除前端原生 `window.alert / window.confirm`：
  - 新增统一站内弹窗 `app-dialog-modal`
  - 删除确认、批量删除确认、设置保存提示、API 检测失败提示均改为平台自身蓝白风格弹窗
- 已新增批量删除能力：
  - 首页 `已完成任务` 支持多选并 `批量删除历史任务`
  - `审计项目` 页支持多选并 `批量删除任务`
  - `知识库` 页支持多选并 `批量删除历史`
  - 单条删除与批量删除共用同一套前端确认流程与后端删除接口
- 已新增上传样本自动清理：
  - 当会话状态进入 `completed` 或 `failed` 后，若目标来自平台上传的 `artifact_id`，会自动删除对应上传样本文件与 artifact 元数据
  - 不会删除用户手工指定的外部 `target_path`
- 当前已再次验证：
  - `node --check frontend/static/app.js` 通过
  - `./.venv/bin/pytest -q` 通过，当前结果：`46 passed`
  - 真实 `http://127.0.0.1:10000/` 已确认输出：
    - `批量删除任务`
    - `批量删除历史任务`
    - `批量删除历史`
    - `保存 API Key`
    - `app-dialog-modal`
  - 真实 `http://127.0.0.1:10000/static/app.js` 已确认包含：
    - `confirmAction`
    - `handleBulkDeleteSelectedProjects`
    - `handleBulkDeleteKnowledgeEntries`
  - 真实 `http://127.0.0.1:10000/api/v1/runtime` 返回仍为：
    - `llm_backend=DeepSeekLLMBackend`
    - `llm_provider=deepseek`
    - `docker_runtime=true`

## 2026-05-03

### 本次完成

- 从空目录搭建了后端 MVP 骨架
- 建立了 `FastAPI` API 服务与基础数据模型
- 实现了中央 `ManagerAgent` 的任务创建、核心笔记生成、子任务拆分与并行调度
- 实现了 `Sub-Agent` 运行骨架，支持本地进程模式与 Docker 隔离模式
- 实现了三类观察者：
  - 工具调用防沉迷
  - 笔记重复检索清除
  - 长上下文重置
- 接入了 `DeepSeek` 模型路由层，并保留无 Key 时的 `MockLLM` 回退
- 增加了上传样本、创建审计、查询会话、读取进度文档等接口
- 增加了浏览器前端，支持上传样本、发起审计、查看会话详情、轮询状态和阅读开发进度
- 将默认访问端口从 `8000` 切换为 `10000`，统一了容器启动、端口映射与 README 使用说明
- 补充了 `README`、`ARCHITECTURE`、`Dockerfile`、`docker-compose` 等工程文件

### 当前状态

- 项目已经具备“可运行后端骨架”
- 已具备“可直接交互的 Web 控制台”
- 重点完成的是编排架构，不是完整漏洞分析能力
- 现在的工具证据采样仍以 `file/readelf/strings` 为主

### 下一步建议

1. 接入真实漏洞分析工具链：`checksec`, `rizin`, `gdb`, `AFL++`, `angr`
2. 给前端增加 WebSocket 事件流，实时展示各子代理进度和干预事件
3. 引入任务队列和多机 worker 调度，做真正的分布式执行层
4. 增加结果结构化输出，将漏洞发现沉淀为规则化审计报告

### 增量进展（2026-05-03 15:55:51 UTC）

- 已补上实时事件总线与 WebSocket 接口，前端可直接订阅审计事件流，并保留轮询回退
- 已接入工具能力清单接口，前端可显示当前宿主机可用的分析工具
- 已扩展二进制工具箱，纳入 `checksec`、`gdb`、`AFL++`、`IDA`、`angr` 能力探测与执行路径
- 已完成 `angr` 在项目 `.venv` 中的重新安装，当前版本为 `9.2.213`
- 已修复 `app/toolbox.py` 中 `angr_cfg` 对 `cle` 段对象属性的兼容性问题，`/bin/ls` 烟雾测试已返回 `completed`
- 当前已验证：`pytest -q` 通过，结果为 `8 passed`
- 已将平台内置 `ida_batch` 改为优先复用 `/home/tankuku/rootfs_elf/ida_worker.py`，输出 `strings/imports/exports/source.c/function_index` 等更完整产物
- 已为 Docker 子代理补充 `rootfs_elf` 目录挂载与环境变量透传，避免容器内退回旧的简化 IDA 路径
- 当前已验证：`ida_batch` 对 `/bin/ls` 返回 `completed`，且 `metadata.exporter = rootfs_elf`

### 增量进展（2026-05-03 17:12:00 UTC）

- 已补充会话报告导出接口：`GET /api/v1/audits/{session_id}/report`
- 已支持两种导出格式：
  - `format=markdown`：导出 Manager 汇总报告
  - `format=json`：导出带核心笔记、子代理摘要、证据与最终报告的结构化结果
- 已为前端会话详情页增加 `导出 Markdown` / `导出 JSON` 按钮
- 已为应用入口补充 `create_app(settings_override)`，便于隔离测试数据目录并做集成测试
- 已新增审计主链路集成测试，覆盖“创建会话 -> 子代理完成 -> 导出报告”
- 当前已验证：`./.venv/bin/pytest -q` 通过，结果为 `9 passed`
- 已使用 `/home/tankuku/timu/pwn/attachment_2/pwn` 完成一次完整 agent 验证：
  - `difficulty=hard`
  - `max_subagents=4`
  - 覆盖 `triage/static-analysis/dynamic-analysis/exploit-strategy`
  - 已确认 `checksec` / `gdb` / `AFL++` / `angr` / `IDA` 工具链均进入调用路径
  - `ida_batch` 返回 `completed`，且继续走 `rootfs_elf` 导出器
  - WebSocket 已返回 `connected` / `tool_inventory` / `session_snapshot`
  - 报告导出已返回 `.md` 与 `.json` 附件响应头
- 本次真实样本验证中的观测结果：
  - `rizin_overview` 仍为 `unavailable`
  - `afl_showmap_probe` 在该题上返回 `failed`，`map_size_bytes=0`
  - `angr` 仍提示 `unicorn` 加速组件未启用，但 `CFGFast` 结果正常产出

### 增量进展（2026-05-03 17:29:00 UTC）

- 已将无 `DEEPSEEK_API_KEY` 时的 `MockLLM` 回退改为“本地证据驱动总结器”
- 新的本地总结逻辑会直接读取 `file/checksec/readelf/gdb/AFL++/angr/IDA` 的真实输出，并按子代理角色生成差异化结论
- 已修复此前“多个子代理摘要几乎相同、看不出真实分析进展”的问题
- 已在本地总结中显式标注当前未调用远端模型，避免前端只显示模型路由而误导用户
- 已移除前端中的 `PROGRESS.md` 展示区块，避免把开发进度文档暴露给终端用户
- 已优化前端实时渲染与滚动性能：
  - WebSocket 事件改为节流后刷新详情区
  - 实时事件列表数量进一步收敛
  - 移除了大面板的 `backdrop-filter` 模糊效果
  - 为重内容卡片增加 `content-visibility`
- 已补充测试覆盖：
  - 首页不再显示“开发进度文档”
  - 本地总结器会根据不同证据生成不同摘要
- 当前已验证：`./.venv/bin/pytest -q` 通过，结果为 `10 passed`
- 已再次使用 `/home/tankuku/timu/pwn/attachment_2/pwn` 完成完整 agent 验证：
  - `triage/static-analysis/dynamic-analysis/exploit-strategy` 已输出明显不同的摘要
  - `angr_cfg` 在当前 `.venv` 运行时中返回 `completed`
  - 报告导出仍可返回 `.md` 附件响应头
  - `rizin_overview` 仍为 `unavailable`
  - `afl_showmap_probe` 仍因目标执行条件不足返回 `failed`

### 增量进展（2026-05-03 17:42:00 UTC）

- 已新增 `GET /api/v1/runtime`，前端可直接显示当前运行时是否真正接入 `DeepSeek`
- 已确认当前 `10000` 端口运行进程的 `/api/v1/runtime` 返回：
  - `llm_backend = DeepSeekLLMBackend`
  - `llm_provider = deepseek`
  - `llm_configured = true`
- 已将前端“会话详情”重构为更简洁的工作台视图：
  - 概览卡片
  - `Agent Workbench`
  - 关键事件
  - 折叠的 Manager 报告
- 已移除原先大段重复铺开的子代理全文摘要，改为重点发现 + 实时工作 + 工具状态 + 按需展开证据
- 已为运行时面板增加 `LLM 后端` 与 `模型路由` 可视化状态
- 已进一步收紧 `DeepSeek` 提示词：
  - 禁止把外部知识伪装成已验证事实
  - 禁止引用未在工具证据中出现的哈希对照、公开资料、发行版结论
  - 推断必须显式标记为“推断”
- 已用真实 `DeepSeek` 运行最小烟雾会话，确认服务不再走本地回退
- 当前已验证：`./.venv/bin/pytest -q` 通过，结果为 `11 passed`

### 增量进展（2026-05-03 17:56:00 UTC）

- 已修复前端对 `DeepSeek` 摘要的解析问题：
  - 现在可正确解析 `*` 列表、`###` 标题和编号段落
  - 不再错误显示“尚未产出可展示的摘要”
- 已为会话详情补充历史事件回填：
  - 老会话在没有实时 WebSocket 增量时，仍会显示子代理历史事件与 Manager 历史事件
  - 不再错误显示“等待实时事件”
- 已将子代理全文摘要和 Manager 报告改为普通阅读排版，不再默认使用大块等宽代码样式
- 已在会话详情中增加 `样本文件` 字段，降低“上传文件与分析目标不一致”的辨识成本
- 已清理之前为联调创建的内部 smoke 会话记录：
  - `deepseek live smoke`
  - `toolchain smoke`
  - `ls smoke test`
- 当前 `GET /api/v1/audits` 仅保留用户真实创建的 `样本初始审计` 会话
- 当前已验证：
  - `./.venv/bin/pytest -q` 通过，结果为 `11 passed`
  - `GET /api/v1/runtime` 仍返回 `DeepSeekLLMBackend`

### 增量进展（2026-05-03 18:05:00 UTC）

- 已修复前端“会话详情互相遮挡”的布局问题：
  - 移除了卡片上的 `content-visibility` 与 `contain-intrinsic-size`
  - 为详情卡片、时间线、工作台和报告区补齐 `min-width: 0` 与安全换行
  - 将详情元信息网格改为 `auto-fit`，避免中等宽度屏幕上的卡片重叠
- 已调整主工作区布局：
  - 左侧会话栏改为固定窄列
  - 右侧详情区吃满剩余宽度
  - 左侧会话栏增加吸顶与独立滚动，避免“大屏左半边空置”的观感
- 已进一步中文化用户界面：
  - 首页标题、副标题、区块标签改为中文
  - 工作台、关键事件、管理代理报告等用户侧标题改为中文
  - 工具状态 `available/unavailable` 改为 `可用/不可用`
  - 报告导出后的 Manager 汇总标题与字段改为中文
- 已将会话详情中的全文摘要与报告从等宽代码块切换为普通阅读排版
- 已清理我此前创建的内部 smoke 会话，避免 `/bin/ls` 等联调用例继续出现在用户会话列表
- 已完成一次临时目录下的完整 agent 回归验证：
  - 样本：`/home/tankuku/timu/pwn/attachment_2/pwn`
  - 验证项：工具调用、DeepSeek 摘要、Markdown 报告导出
  - 结果：`completed`
- 当前已验证：
  - `./.venv/bin/pytest -q` 通过，结果为 `11 passed`
  - pwn 样本导出报告抬头已为中文，例如 `## 管理代理摘要`

### 当前阻塞

- `angr` 导入时会提示 `unicorn` 加速组件未启用，但不影响当前 `CFGFast` 路径
- `.env.example` 仍需补充更完整的运行时说明

### 增量进展（2026-05-03 18:14:12 UTC）

- 已将“子代理工作台”改为横向卡片工作台：
  - `agent-grid` 改为横向 `flex` 布局
  - 开启 `overflow-x: auto` 横向滚动
  - 子代理卡片固定为单张横向阅读宽度，避免继续竖向堆叠
  - 补充 `scroll-snap` 与触摸滚动优化，横向浏览更稳定
- 已清理移动端样式中对 `agent-grid` 的无效栅格声明，避免后续维护时误改回竖排
- 当前 `http://127.0.0.1:10000/static/styles.css` 已确认输出最新横向样式，无需重启服务，只需浏览器强制刷新
- 已完成一次隔离数据目录下的完整 agent 回归验证：
  - 样本：`/home/tankuku/timu/pwn/attachment_2/pwn`
  - 会话标题：`横向工作台回归验证`
  - 会话结果：`completed`
  - 子代理结果：`triage` / `static-analysis` / `exploitability-review` 全部 `completed`
  - 工具链结果：
    - `file` / `sha256` / `checksec` / `elf_header` / `section_headers` / `symbol_table` / `ida_batch` / `angr_cfg` / `strings_preview` / `gdb_batch` 全部 `completed`
    - `rizin_overview` 仍因环境未安装返回 `unavailable`
  - 报告导出结果：
    - Markdown 导出成功
    - JSON 导出成功
    - `Content-Disposition` 附件响应头正常返回
  - LLM 运行态：
    - `llm_backend = DeepSeekLLMBackend`
    - `llm_provider = deepseek`
    - `llm_configured = true`
- 当前已再次验证：`./.venv/bin/pytest -q` 通过，结果为 `11 passed`

### 增量进展（2026-05-03 21:10:00 UTC）

- 已把线上 `10000` 端口服务切到最新运行时配置：
  - `GET /api/v1/runtime` 现返回 `docker_runtime=true`
  - `llm_backend=DeepSeekLLMBackend`
  - `llm_provider=deepseek`
  - 已确认不再是旧进程残留导致的“代码已改、服务未生效”
- 已收口用户面暴露：
  - 删除 `GET /api/v1/progress`
  - 开发进度文档 `docs/PROGRESS.md` 不再通过 API 直接暴露给前端用户
- 已增强最终报告净化逻辑：
  - 子代理摘要在落库前会过滤“下一步 / 后续 / 建议 / 需进一步 / 可继续 / 继续分析”等动作性语句
  - 导出的 Markdown / JSON 报告已确认不再包含“下一步建议”
  - 过滤后仍保留函数级证据、利用性判断和核心结论
- 已修复 Docker 子代理真实运行时故障：
  - 根因：宿主机 `~/.idapro/plugins/INP.py` 为悬空软链，复制 `.idapro` 到容器运行目录时触发 `FileNotFoundError`
  - 修复：`DockerSubAgentRuntime._prepare_ida_user_dir()` 改为 `shutil.copytree(..., ignore_dangling_symlinks=True, dirs_exist_ok=True)`
  - 结果：不再因宿主机历史 IDA 插件残留导致整场审计会话在启动阶段失败
- 已进一步清理管理代理“关键结论”质量：
  - promoted notes 提取时新增过滤纯节标题项
  - 例如 `利用性判断`、`已验证发现`、`关键函数深度分析` 不会再被误提升为核心结论 bullet
- 已完成容器级工具链复验：
  - `rabin2 -jI` 在 `binary-audit-subagent:latest` 内可直接返回结构化 ELF 信息
  - `radare2 -q -c 'aa;aflj'` 在容器内可直接返回函数列表
  - `rootfs_elf/ida_worker.py` 在容器内成功导出：
    - `data_symbols.txt`
    - `exports.txt`
    - `function_index.jsonl`
    - `imports.txt`
    - `source.c`
    - `strings.txt`
- 已完成本轮 `pwn` 样本的真实端到端最终验收：
  - 样本：`/home/tankuku/timu/pwn/attachment_2/pwn`
  - 会话标题：`pwn 附件最终验收`
  - 会话 ID：`ed2ae24d912245e99f496ebe24811b57`
  - 会话结果：`completed`
  - 四个 Docker 子代理全部完成并回填 `container_id`
  - agent 间协作已真实发生：
    - 每个子代理均出现 `agent_message_sent`
    - 每个子代理均出现 `agent_message_received`
    - 会话级协调目录真实生成多条 `plan / evidence / summary` 广播消息
  - 多轮取证已真实发生，而不是单轮总结：
    - `triage`：`file` / `sha256` / `checksec` / `elf_header` / `rizin_overview` 后继续执行 `function_disasm`、`function_xrefs`
    - `static-analysis`：`section_headers` / `symbol_table` / `ida_batch` / `angr_cfg` 后继续执行 `function_disasm`、`function_xrefs`
    - `exploit-strategy`：`strings_preview` / `section_headers` / `ida_batch` 后继续执行 `function_disasm`、`function_xrefs`
  - 最终漏洞结论已下沉到函数级：
    - `main@0x4011b6`
    - `read(0, buf, 0x100)` 把用户输入写入 `.bss` 全局缓冲区 `buf@0x404080`
    - `printf(buf)` 直接把可控 `buf` 当格式串使用
    - 综合 `No PIE + Partial RELRO + No canary + 可写 GOT`，报告已给出高可利用格式化字符串漏洞结论
  - 动态工具状态：
    - `gdb_batch=completed`
    - `rizin_overview=completed`
    - `ida_batch=completed`
    - `angr_cfg=completed`
    - `function_xrefs=completed`
    - `afl_showmap_probe=failed`（样本交互方式导致 forkserver 未建立，已在报告中作为已知动态限制保留）
  - 报告导出验证：
    - Markdown 导出 `200`
    - JSON 导出 `200`
    - 导出内容已确认不含“下一步”/“建议”
- 已补充回归测试：
  - `tests/test_session_flow.py::test_progress_document_is_not_exposed_by_api`
  - `tests/test_manager_report.py::test_manager_sanitizes_next_step_language_from_subagent_summary`
  - `tests/test_coordination.py::test_prepare_ida_user_dir_ignores_dangling_symlinks`
  - `tests/test_subagent.py::test_extract_promoted_notes_skips_section_heading_bullets`
- 当前已再次验证：
  - `./.venv/bin/pytest -q` 通过，结果为 `25 passed`
  - `./.venv/bin/python -m py_compile app/config.py app/routes.py app/manager.py app/subagent.py app/toolbox.py app/llm.py` 通过

### 增量进展（2026-05-03 19:27:00 UTC）

- 已补充本地 `.env` 运行时配置，重启后仍会自动读取 `DeepSeek` Key，不再依赖手工前缀注入
- 已清理残留 `uvicorn` 进程并重启 `10000` 端口在线服务，当前仅保留单实例监听
- 已确认在线运行态：
  - `GET /api/v1/runtime` 返回 `llm_backend = DeepSeekLLMBackend`
  - `GET /api/v1/runtime` 返回 `llm_configured = true`
  - `GET /api/v1/tools` 返回 `rizin_overview.available = true`
- 已将子代理执行链升级为“基础采样 + 两轮函数级 refinement + 最终综合”：
  - round 1：`function_disasm`，通过 `objdump` 对焦点函数做地址区间反汇编、栈帧与参数关系提取
  - round 2：`function_xrefs`，通过 `radare2 axtj` 补齐函数调用者与交叉引用
- 已将 `function_disasm` / `function_xrefs` 接入 follow-up 规划与最终摘要解释：
  - 可识别 `overflow-candidate`
  - 可识别 `format-string`
  - 可提炼 `函数深度分析` / `函数风险` / `函数交叉引用`
- 已收紧最终报告输出策略：
  - 子代理最终摘要不再输出“下一步建议”
  - 最终摘要固定收敛为“已验证发现 / 关键函数深度分析 / 利用性判断 / 值得提升为核心笔记的结论”
  - Manager 汇总新增 `## 关键结论`
- 已继续收敛报告顶部摘要：
  - `关键结论` 会对跨子代理重复结论做轻量去重
  - 不再把“第一次溢出”“证据来源”这类利用推演或证据清单直接抬到顶部摘要
- 已原地重跑在线 `clock_in` 历史会话，修复旧报告仍停留在表层建议的问题：
  - 会话：`8c2870a81e4c40f8867abbe2da5d7940`
  - 会话：`f68600c3df024eb8b3d28b8a616f6493`
  - 两条会话的 `triage/static-analysis/exploitability-review` 现均包含 `function_disasm` / `function_xrefs`
  - 两条会话导出报告均已确认：
    - 不包含“下一步建议”
    - 包含“函数深度分析”
    - 包含 `## 关键结论`
  - `f686...` 当前报告已直接落到函数级结论：
    - `sym.get_info` 中 `fgets` 允许读取 `0x100` 字节写入 `[rbp-0x40]` 的 `0x40` 字节栈缓冲区
    - `checksec` 证实 `No canary` 且 `No PIE`
    - 报告已明确给出“栈缓冲区溢出已证明存在”的结论
- 已完成一次隔离数据目录下的完整 agent 验证：
  - 样本：`/home/tankuku/timu/pwn/attachment_2/pwn`
  - 会话标题：`隔离完整 agent 验证`
  - 会话结果：`completed`
  - 子代理角色：`triage` / `static-analysis` / `dynamic-analysis` / `exploit-strategy`
  - 工具链结果：
    - `triage`：`file` / `sha256` / `checksec` / `elf_header` / `rizin_overview` / `function_disasm` / `function_xrefs` 全部 `completed`
    - `static-analysis`：`section_headers` / `symbol_table` / `ida_batch` / `angr_cfg` / `function_disasm` / `function_xrefs` 全部 `completed`
    - `dynamic-analysis`：`program_headers` / `dynamic_section` / `gdb_batch` 为 `completed`，`afl_showmap_probe` 为 `failed`
    - `exploit-strategy`：`strings_preview` / `section_headers` / `ida_batch` / `function_disasm` / `function_xrefs` 为 `completed`，`afl_showmap_probe` 为 `failed`
  - 报告导出链路已验证：
    - Markdown 报告已生成
    - JSON 导出对象已生成
    - 最终报告包含 `函数深度分析`
    - 最终报告不包含“下一步建议”
- 已补充新的回归测试：
  - `tests/test_subagent.py`：覆盖 promoted notes 仅提升核心结论、过滤“下一步建议/第一次溢出”
  - `tests/test_manager_report.py`：覆盖管理代理 `关键结论` 的重复结论去重
- 当前已再次验证：`./.venv/bin/pytest -q` 通过，结果为 `17 passed`

### 增量进展（2026-05-03 20:10:00 UTC）

- 已把“中央 `ManagerAgent` + 多 `Sub-Agent` 独立容器 + agent 间通信”这条链路补成真实实现，而不再只是并行执行骨架
- 已新增会话级协作信箱：
  - 目录：`data/runtime/<session>/coordination`
  - 载体：结构化 `json` 消息文件
  - 广播阶段：`plan` / `evidence` / `summary`
  - 每个子代理会把同伴阶段性结论吸收为独立普通笔记，但仍保留自己的上下文窗口与判断路径
- 已在 `SubAgentWorker` 内接入真实通信轮次：
  - 计划生成后广播 `plan`
  - 证据采样与 refinement 完成后广播 `evidence`
  - 最终综合完成后广播 `summary`
  - 接收方会写入 `peer:<role>` 来源笔记，并在后续综合阶段一起进入 `LLM` 输入
- 已在 `DockerSubAgentRuntime` 中补齐容器级共享挂载：
  - 为每个会话单独挂载 `/coordination`
  - `SUBAGENT_DOCKER_NETWORK_MODE=auto`
  - 已配置远端 `DeepSeek` Key 时自动切到 `bridge`
  - 未配置 Key、走本地回退时自动回到 `none`
  - 继续保留每个子代理独立 `/runtime`
  - 通过 `--cidfile` 回写真实容器 ID
- 已新增协作事件类型：
  - `agent_message_sent`
  - `agent_message_received`
- 已为前端补上上述事件的中文标签与工作状态文案，并更新静态资源版本：
  - `styles.css?v=20260503f`
  - `app.js?v=20260503f`
- 已修复协作邮箱的并发一致性问题：
  - 消息文件改为“先写临时文件，再原子替换”
  - 避免并发子代理读到半截 JSON 导致任务失败
- 已补充回归测试：
  - `tests/test_coordination.py::test_agent_mailbox_publishes_and_drains_messages`
  - `tests/test_coordination.py::test_subagents_exchange_messages_via_shared_coordination_dir`
  - `tests/test_coordination.py::test_docker_runtime_mounts_coordination_dir_and_reads_cidfile`
  - 继续保留此前关于 `ToolLoopObserver` / `NoteRecallObserver` / `ContextWindowObserver` 的纠偏测试
- 当前已再次验证：`./.venv/bin/pytest -q` 通过，结果为 `20 passed`

### 增量进展（2026-05-03 18:46:13 UTC）

- 已解决 `rizin_overview` 报告中长期显示 `unavailable` 的问题，改为真实调用 `radare2/rabin2`
- 已将 `rizin_overview` 的真实调用链路改为：
  - `rabin2 -jI/-jl/-ji` 采集基础元数据、动态依赖与导入表
  - `radare2 -q -c 'aa;axtj ...'` 采集危险导入函数的真实交叉引用调用点
- 已将工具发现逻辑扩展为优先搜索项目内用户态安装：
  - 本地路径：`.vendor/radare2/root/usr/bin`
  - 不再强依赖宿主机 `apt install`
- 已在项目内完成用户态安装：
  - `radare2_5.5.0+dfsg-1.1ubuntu3_amd64.deb`
  - `libradare2-5.0.0t64_5.5.0+dfsg-1.1ubuntu3_amd64.deb`
  - `libradare2-common_5.5.0+dfsg-1.1ubuntu3_all.deb`
  - `libzip4t64_1.7.3-1.1ubuntu2_amd64.deb`
  - 解包位置：`.vendor/radare2/root`
- 已确认当前 `http://127.0.0.1:10000/api/v1/tools` 返回：
  - `rizin_overview.available = true`
  - `rizin_overview.executable = /home/tankuku/agent/.vendor/radare2/root/usr/bin/radare2`
- 已同步 Docker 构建环境：
  - `Dockerfile.manager` 安装 `radare2`
  - `Dockerfile.subagent` 安装 `radare2`
- 已补充本地总结器对 `rizin_overview` 结构化输出的解释：
  - `Rizin 动态依赖`
  - `Rizin 危险导入`
  - `Rizin 调用点`
- 已完成本轮验证：
  - `./.venv/bin/pytest -q` 通过，结果为 `12 passed`
  - `BinaryToolbox._build_capability("rizin_overview")` 已识别 vendored `radare2`
  - 直接工具实跑结果：
    - `info_backend = rabin2`
    - `analysis_backend = radare2`
    - `linked_libraries = [\"libc.so.6\"]`
    - `dangerous_imports = [\"printf\", \"read\"]`
    - `dangerous_xrefs = [\"printf\", \"read\"]`
  - 隔离数据目录下完整 agent 验证：
    - 样本：`/home/tankuku/timu/pwn/attachment_2/pwn`
    - 会话标题：`rizin 真实调用回归验证`
    - 会话结果：`completed`
    - `triage.rizin_overview.status = completed`
    - 导出报告中已不再出现 `rizin_overview=unavailable`
    - 导出报告已能命中 `Rizin` 相关证据段

### 增量进展（2026-05-03 18:25:16 UTC）

- 已将子代理工作台进一步收敛为“横向极简进度卡”：
  - `agent-grid` 从横向 `flex` 收紧为横向自动列网格，固定按列展开，避免再次出现竖向堆叠观感
  - 子代理卡片仅展示：
    - 子代理角色
    - 当前阶段
    - 任务进度
    - 当前工作状态
  - 已移除子代理卡片中的大段摘要、工具状态 chips、事件列表、完整证据折叠区，降低信息噪音
- 已将状态文案进一步中文化：
  - 子代理状态 `queued/running/completed/failed` 改为中文显示
  - 事件流中的事件类型标题改为中文显示
  - 会话顶部状态与首页最近状态改为中文显示
- 已将管理代理完整报告改为默认折叠，避免详情页首次打开时内容过长造成视觉拥挤
- 已对静态资源增加版本号：
  - `styles.css?v=20260503e`
  - `app.js?v=20260503e`
  - 用于强制浏览器获取最新横向布局和极简工作台脚本，避免继续命中旧缓存
- 当前已确认 `http://127.0.0.1:10000/` 首页实际输出上述新版本静态资源引用，服务端已生效
- 已完成本轮隔离数据目录下的完整 agent 回归验证：
  - 样本：`/home/tankuku/timu/pwn/attachment_2/pwn`
  - 会话标题：`极简横向工作台回归验证`
  - 会话结果：`completed`
  - 子代理结果：`triage` / `static-analysis` / `exploitability-review` 全部 `completed`
  - 工具链结果：
    - `file` / `sha256` / `checksec` / `elf_header` / `section_headers` / `symbol_table` / `ida_batch` / `angr_cfg` / `strings_preview` / `gdb_batch` 全部 `completed`
    - `rizin_overview` 仍因环境未安装返回 `unavailable`
  - 报告导出结果：
    - Markdown 导出成功
    - JSON 导出成功
    - `Content-Disposition` 附件响应头正常返回
  - LLM 运行态：
    - `llm_backend = DeepSeekLLMBackend`
    - `llm_provider = deepseek`
    - `llm_configured = true`
- 当前已再次验证：`./.venv/bin/pytest -q` 通过，结果为 `11 passed`

## 2026-05-04

### 增量进展（2026-05-04 05:41:00 UTC）

- 已移除 `DeepSeek` 缺失时的本地总结回退路径：
  - `app/llm.py` 中 `create_llm_backend()` 现在只允许真实 `DeepSeek` 后端
  - 未配置 Key 时返回 `MissingDeepSeekLLMBackend`，不再静默落回本地总结器
- 已同步更新运行态与前端运行态展示：
  - `app/manager.py` 的 `/api/v1/runtime` 明确返回 `llm_status`
  - `frontend/static/app.js` 不再向用户暴露“本地回退模式”文案
- 已重构最终报告拼装逻辑，确保结果下沉到函数级而不是停留在子代理表层摘要：
  - `Manager` 现在会综合 `function_disasm`、`function_xrefs`、`rizin_overview`、`ida_batch`、`angr_cfg`
  - 导出 Markdown / JSON 的 `report_markdown` 已稳定包含 `main @ 0x4011b6` 等函数级取证段落
- 已继续收紧报告净化规则，过滤所有未完成或条件性语言：
  - 过滤词从“下一步 / 建议”扩展到 `必要时`、`如需`、`疑似`、`若存在`、`未知漏洞`、`未建立利用上下文`、`只要补全`、`即可立即`
  - 新增对 `：若...`、`如果...`、`否则若...` 这类条件句的统一拦截
  - `SubAgent` 的 promoted notes 提取与 `Manager` 的最终报告筛选已使用同一套规则
- 已补充回归测试覆盖上述收口逻辑：
  - `tests/test_llm.py`：校验缺失 `DeepSeek` Key 时不再回退到本地总结器
  - `tests/test_manager_report.py`：校验最终报告过滤条件性/未完成结论
  - `tests/test_subagent.py`：校验 promoted notes 不再提升条件性或行动性句子
- 当前已再次验证：`./.venv/bin/pytest -q` 通过，结果为 `29 passed`

### 真实端到端验收（固定样本）

- 验证样本：`/home/tankuku/timu/pwn/attachment_2/pwn`
- 最终验收会话：
  - 标题：`2026-05-04 pwn 附件最终验收 v8`
  - 会话 ID：`278a2c8eadda4f828103ba88c82b4599`
  - 会话结果：`completed`
- 在线运行态已确认：
  - `GET /api/v1/runtime` 返回 `llm_backend=DeepSeekLLMBackend`
  - `GET /api/v1/runtime` 返回 `llm_provider=deepseek`
  - `GET /api/v1/runtime` 返回 `llm_status=ready`
  - `GET /api/v1/runtime` 返回 `docker_runtime=true`
  - `GET /api/v1/progress` 返回 `404`
- Docker 子代理已真实运行并落盘 `container_id`：
  - `triage`: `4b3e3d9789a1...`
  - `static-analysis`: `2de545833f07...`
  - `dynamic-analysis`: `58838fa248f2...`
  - `exploit-strategy`: `4a0a23092b90...`
- agent 间协作已真实发生：
  - `agent_message_sent = 12`
  - `agent_message_received = 30`
  - 会话级 coordination mailbox 真实生成 `12` 个消息文件
- 关键工具证据已真实落盘并进入 `result.json` / 会话导出：
  - `function_disasm = 3`
  - `function_xrefs = 3`
  - `ida_batch = 2`
  - `angr_cfg = 1`
  - `rizin_overview = 1`
  - `ida_batch` 继续走 `rootfs_elf` 导出器，产物包含：
    - `data_symbols.txt`
    - `exports.txt`
    - `function_index.jsonl`
    - `imports.txt`
    - `source.c`
    - `strings.txt`
- 导出链路已确认可用：
  - Markdown 导出 `200`，带 `Content-Disposition` 附件头
  - JSON 导出 `200`，带 `Content-Disposition` 附件头
  - `report_markdown` 已确认不含“下一步”“建议”“必要时”“疑似”“若存在”“只要补全”“未知漏洞”“未建立利用上下文”
- 本轮最终函数级结论已确认：
  - `main@0x4011b6` 中 `read(0, buf, 256)` 将用户输入写入 `.bss` 全局缓冲区 `buf@0x404080`
  - `main@0x40124f` 直接执行 `printf(buf)`
  - 结合 `No PIE`、`Partial RELRO`、`No Canary`、可写 GOT，最终报告已给出格式化字符串漏洞与利用链结论

### 增量进展（2026-05-04 06:44:00 UTC）

- 已重构中央 `ManagerAgent` 的会话编排入口：
  - 在真正分配子代理前，先调用 `DeepSeek` 生成会话级 orchestration plan
  - 规划结果会落盘到 `session.manager_plan_summary`
  - 子任务不再只按难度标签硬编码生成，而是带上：
    - 角色专属 objective
    - `coordination_focus`
    - `collaboration_targets`
- 已把子代理协作从“固定节点单次广播”扩展为“多轮自由通信”：
  - `AgentMailbox` 新增定向投递与消息元数据：
    - `message_kind`
    - `topic`
    - `recipients`
    - `requires_response`
    - `in_reply_to`
  - `SubAgent` 现在会在多个阶段真实产生并消费：
    - `plan`
    - `update`
    - `question`
    - `answer`
    - `summary`
  - 同伴消息已接入 follow-up 规划，`toolbox.plan_follow_up()` 会读取 peer note 中共享的函数名/地址，驱动下一轮 `function_disasm` / `function_xrefs`
- 已修正 mailbox 闭环中的“隐式吞消息”问题：
  - 普通 `update/summary` 发送后不再顺手把 inbox 消息吃掉
  - 这样 peer question 会留到下一轮协作或 synthesis 前显式触发 `answer`
- 已增强前端工作台与事件流展示：
  - 会话详情新增折叠的 `管理代理分工`
  - 子代理卡片新增 `协作状态`，压缩展示 `发/收` 计数与最近协作动作
  - 时间线事件文案已按 `manager planning / tool / mailbox` 语义翻成中文
  - 静态资源版本号已更新为：
    - `styles.css?v=20260504b`
    - `app.js?v=20260504b`
- 已补充回归测试：
  - `tests/test_manager_planning.py`：校验 Manager 会话规划结果会驱动任务生成
  - `tests/test_coordination.py`：校验 mailbox 定向投递与多类消息
  - `tests/test_toolbox.py`：校验 peer-shared focus function 可进入 follow-up 规划
  - 当前已验证：`./.venv/bin/pytest -q` 通过，结果为 `31 passed`

### 最新真实端到端验收（固定样本）

- 验证样本：`/home/tankuku/timu/pwn/attachment_2/pwn`
- 最新验收会话：
  - 标题：`2026-05-04 深协作通信回归验收 v3`
  - 会话 ID：`cbdbdd417ea24fa3a565b1ca4d1fecb5`
  - 会话结果：`completed`
- 在线运行态已再次确认：
  - `GET /api/v1/runtime` 返回 `llm_backend=DeepSeekLLMBackend`
  - `GET /api/v1/runtime` 返回 `llm_provider=deepseek`
  - `GET /api/v1/runtime` 返回 `llm_status=ready`
  - `GET /api/v1/runtime` 返回 `docker_runtime=true`
  - `GET /api/v1/progress` 返回 `404`
- `ManagerAgent` 深度分工已真实生效：
  - `manager_plan_summary` 已写入会话快照
  - 本轮角色集合为：
    - `triage`
    - `static-analysis`
    - `dynamic-analysis`
    - `exploit-strategy`
- Docker 子代理已真实运行并全部落盘 `container_id`
- mailbox 多轮协作已真实发生：
  - coordination 目录落盘 `29` 个消息文件
  - `agent_message_sent = 29`
  - `agent_message_received = 59`
  - 消息类型分布：
    - `plan = 4`
    - `update = 12`
    - `question = 6`
    - `answer = 4`
    - `summary = 3`
  - 角色发送计数：
    - `triage = 7`
    - `static-analysis = 6`
    - `dynamic-analysis = 8`
    - `exploit-strategy = 8`
  - 已确认不再是“完成后只通信一次”的旧行为，当前真实链路已包含：
    - `plan -> update -> question -> answer -> summary`
- 导出链路已再次确认可用：
  - Markdown 导出 `200`，带 `Content-Disposition` 附件头
  - JSON 导出 `200`，带 `Content-Disposition` 附件头
- 最终报告约束已再次确认：
  - `report_markdown` 包含 `## 函数级取证结论`
  - `report_markdown` 包含 `### main @ 0x4011b6`
  - `report_markdown` 不含“下一步”

### 增量进展（2026-05-04 07:45:00 UTC）

- 已把外部 `ctf-pwn` skill 包接入平台运行时：
  - `app/config.py` 新增 `skill_data_dir`、`pwn_skill_zip_path`、`pwn_skill_dirname`
  - `app/pwn_skill.py` 现会自动解压 `/home/tankuku/ctf-pwn-skill-with-kb-2026-04-30.zip` 到 `data/skills/ctf-pwn`
  - `Manager` 与 `SubAgent` 会把 skill 中的 GDB / 已验证 PoC 约束注入核心笔记
- 已为 `BinaryToolbox` 补齐真实 `gdb_poc`：
  - round 2 follow-up 现在可从 `function_disasm` 中提取 issue-bearing callsite
  - 对 `format-string` 原语会用脚本化 `gdb -batch` 在危险调用点前下断
  - GDB 会采集：
    - `x/i $pc`
    - `info registers rdi/rsi/rdx/...`
    - `x/s $rdi`
    - `bt`
  - 同时补跑一次真实 stdin 触发，验证程序输出是否实际展开 `%p`
  - `gdb_poc` 证据现会结构化落盘：
    - `validated`
    - `function`
    - `breakpoint`
    - `gdb_observation`
    - `native_probe`
    - `poc.command`
- 已修正多轮协作循环上限问题：
  - 旧逻辑会在第 3 轮 follow-up 前提前 `break`，导致 `gdb_poc` 永远跑不到
  - `app/subagent.py` 现允许：
    - round 0 -> `function_disasm`
    - round 1 -> `function_xrefs`
    - round 2 -> `gdb_poc`
  - 修复后仍保留每轮中途广播 / 协查 / 回应闭环
- 已增强最终报告的 PoC 汇总：
  - `Manager` 新增 `## 已验证 POC`
  - 仅纳入 `gdb_poc.validated = true` 的结果
  - 报告中展示：
    - 命中的 GDB 断点
    - `x/s $rdi` 取证结果
    - 最小触发命令
    - 真实程序输出摘录
  - 用户侧 Markdown 报告中的 PoC 命令已从容器路径归一化为宿主机真实样本路径
- 已补充回归测试：
  - `tests/test_toolbox.py`：校验 round 2 会调度 `gdb_poc`
  - `tests/test_coordination.py`：校验第 3 轮 follow-up 不再被协作循环截断
  - `tests/test_manager_report.py`：校验 `## 已验证 POC` 与宿主机路径归一化
  - 当前已验证：`./.venv/bin/pytest -q` 通过，结果为 `34 passed`

### 最新真实端到端验收（已验证 PoC）

- 验证样本：`/home/tankuku/timu/pwn/attachment_2/pwn`
- 最新验收会话：
  - 标题：`2026-05-04 已验证PoC验收 v2`
  - 会话 ID：`836da0da00d34b4987db25ead69a24a4`
  - 会话结果：`completed`
- 在线运行态已再次确认：
  - `GET /api/v1/runtime` 返回 `llm_backend=DeepSeekLLMBackend`
  - `GET /api/v1/runtime` 返回 `llm_provider=deepseek`
  - `GET /api/v1/runtime` 返回 `llm_status=ready`
  - `GET /api/v1/runtime` 返回 `docker_runtime=true`
  - `GET /api/v1/progress` 返回 `404`
- Docker 子代理已真实运行并全部落盘 `container_id`
- mailbox 多轮协作已真实发生：
  - coordination 目录落盘 `27` 个消息文件
  - `agent_message_sent = 27`
  - `agent_message_received = 30`
  - 消息类型分布：
    - `plan = 4`
    - `update = 11`
    - `question = 4`
    - `answer = 4`
    - `summary = 4`
- 关键工具证据已真实落盘：
  - `function_disasm = 3`
  - `function_xrefs = 3`
  - `gdb_poc = 1`
  - `ida_batch = 2`
  - `angr_cfg = 2`
  - `gdb_batch = 2`
- `gdb_poc` 已真实验证：
  - 命中函数：`main @ 0x4011b6`
  - 断点：`0x40124f <printf@plt 调用前>`
  - `x/s $rdi`：`0x404080 <buf>: "FMT_PROBE.%p.%p.%p.%p\n"`
  - 真实运行输出：`Please checkin first` 后输出 `FMT_PROBE.0x404080.(nil).(nil).(nil)`
- 导出链路与最终报告已再次确认：
  - Markdown 导出 `200`，带 `Content-Disposition` 附件头
  - `report_markdown` 包含 `## 已验证 POC`
  - `report_markdown` 中的 PoC 命令已使用宿主机路径 `/home/tankuku/timu/pwn/attachment_2/pwn`
  - `report_markdown` 不再出现容器内 `/runtime/inputs/...`
  - `report_markdown` 不含“下一步”

### 当前风险

- `gdb_poc` 的原始证据 JSON 仍保留容器内执行时生成的 `poc.command`；当前仅最终 Markdown 报告做了宿主机路径归一化，若后续希望 JSON 导出也直接面向终端用户展示，还需再补一层规范化
- 最新真实验收中，`static-analysis` 子代理虽然会话状态为 `completed`，但 `output_summary` 仍可能为空；当前不会阻断 Manager 的最终函数级汇总，但说明对“远端模型返回空摘要”的自动重试或降级处理仍未补齐

### 增量进展（2026-05-04 09:24:00 UTC）

- 已把“可利用脚本”正式纳入最终报告导出链路：
  - `app/toolbox.py` 的 `gdb_poc` 现会在已验证 `format-string` 结果中追加 `exploit_script`
  - `exploit_script` 结构化包含：
    - `language`
    - `filename`
    - `summary`
    - `content`
    - `expected_output`
  - 当前最小脚本使用 `pwntools` 启动本地样本，发送 `FMT_PROBE.%p.%p.%p.%p`，并断言输出中已出现 `FMT_PROBE.` 与 `0x404080`
- 已把利用脚本下沉到 `Manager` 最终 Markdown 报告：
  - `app/manager.py` 的 `## 已验证 POC` 现会在对应函数下输出 fenced `python` 代码块
  - 报告内脚本中的 `BINARY = '...'` 已统一归一化为宿主机真实样本路径，不再暴露容器内 `/runtime/inputs/...`
- 已修复“已完成会话报告陈旧”问题：
  - `ManagerAgentService._refresh_session_report()` 现在会在 `get_session`、`list_sessions` 与导出接口路径上重算最终报告
  - 已完成会话在不重新跑整场审计的前提下，也会拿到最新的函数级报告与 PoC/脚本段落
- 已补齐前端对脚本代码块的渲染：
  - `frontend/static/app.js` 的 `renderStructuredText()` 现支持三反引号 fenced code block
  - `frontend/index.html` 静态资源版本已更新到 `20260504c`
- 当前已再次验证：
  - `./.venv/bin/pytest -q` 通过，结果为 `34 passed`
  - `./.venv/bin/python -m compileall app tests` 通过

### 最新真实端到端验收（报告含利用脚本）

- 验证样本：`/home/tankuku/timu/pwn/attachment_2/pwn`
- 最新验收会话：
  - 标题：`2026-05-04 已验证PoC验收 v3 exploit-script`
  - 会话 ID：`ead5b88a75eb41ae92caa4d055db32cd`
  - 会话结果：`completed`
- 在线运行态已再次确认：
  - `GET /api/v1/runtime` 返回 `llm_backend=DeepSeekLLMBackend`
  - `GET /api/v1/runtime` 返回 `llm_provider=deepseek`
  - `GET /api/v1/runtime` 返回 `llm_status=ready`
  - `GET /api/v1/runtime` 返回 `docker_runtime=true`
  - `GET /api/v1/progress` 返回 `404`
- mailbox 多轮协作已真实发生：
  - coordination 目录落盘 `33` 个消息文件
  - `agent_message_sent = 33`
  - `agent_message_received = 48`
- 关键工具证据已真实落盘：
  - `function_disasm = 4`
  - `function_xrefs = 4`
  - `gdb_poc = 1`
  - `ida_batch = 2`
  - `angr_cfg = 2`
  - `gdb_batch = 2`
- 导出链路与报告内容已再次确认：
  - Markdown 导出 `200`，带 `Content-Disposition` 附件头
  - JSON 导出 `200`，带 `Content-Disposition` 附件头
  - `report_markdown` 包含 `## 已验证 POC`
  - `report_markdown` 包含 `from pwn import *`
  - `report_markdown` 包含 `BINARY = '/home/tankuku/timu/pwn/attachment_2/pwn'`
  - `report_markdown` 不再出现容器内 `/runtime/inputs/...`
  - JSON 导出的原始证据文本仍可能包含容器内路径，但 `report_markdown` 主体已正常归一化

### 增量进展（2026-05-04 10:30:00 UTC）

- 已补齐“上传样本报告缺少可利用脚本”的两段根因修复：
  - 上传 ELF 样本若缺少执行位，现会在落盘与 Docker 子代理 staging 两侧自动补齐可执行位
  - `gdb_poc` 的本地探针验证不再只扫描截断后的 `stdout_preview`，改为扫描完整输出并单独提取 `probe_line`
- 已新增 `app/target_utils.py`：
  - `looks_like_executable_payload()` 用文件头判断 ELF/PE/脚本等可执行载荷
  - `ensure_target_executable()` 仅对真实可执行样本补 `x` 位，避免误改普通文本
- 已把执行位修复接入以下路径：
  - `app/manager.py`：上传样本落盘后立即补可执行位
  - `app/subagent.py`：Docker 直接复用 `/workspace/...` 样本与 `/runtime/inputs/...` staged 样本都会补可执行位
  - `app/toolbox.py`：`afl_showmap_probe` / `gdb_poc` 执行前再次兜底补可执行位
- 已修复 PoC 脚本生成逻辑对特定样本地址的错误假设：
  - 不再硬编码断言 `0x404080`
  - 改为在 `pwntools` 脚本中定位 `FMT_PROBE` 输出行，并用正则断言真实泄露出的 `0x...` 指针
  - 现可同时适配 `.bss` 缓冲区样本与栈缓冲区格式化字符串样本
- 已增强远端 DeepSeek 调用的超时与故障保留：
  - `app/llm.py` 现对 DeepSeek completion 加硬超时，超时后抛出明确错误
  - `app/subagent.py` 现会在总结阶段失败时保留已采集 `evidence` 与 `plan_summary`，避免整条证据链丢失
- 已补充回归测试并刷新基线：
  - `tests/test_target_utils.py`：覆盖 ELF 补执行位与普通文本不误改
  - `tests/test_session_flow.py`：覆盖上传 ELF 样本落盘后具有执行位
  - `tests/test_coordination.py`：覆盖 Docker 容器目标准备时补执行位，以及总结失败时保留证据
  - `tests/test_toolbox.py`：覆盖完整输出验证 `FMT_PROBE` 与泛化的指针泄露断言
  - `tests/test_llm.py`：覆盖 DeepSeek completion 硬超时
  - 当前已验证：`./.venv/bin/pytest -q` 通过，结果为 `42 passed`
  - 当前已验证：`./.venv/bin/python -m compileall app tests` 通过

### 最新真实端到端验收（上传样本报告含利用脚本）

- 运行态复核：
  - `ss -ltnp` 已确认 `uvicorn` 监听 `0.0.0.0:10000`
  - `GET /api/v1/runtime` 返回：
    - `llm_backend=DeepSeekLLMBackend`
    - `llm_provider=deepseek`
    - `llm_status=ready`
    - `docker_runtime=true`
  - `GET /api/v1/progress` 返回 `404`
- 固定验证样本：`/home/tankuku/agent/data/uploads/6c240c3f5fb5f53f140b4b7945e6870b91d2f944/pwn`
- 样本执行位已复核：
  - `stat` 返回 `775 /home/tankuku/agent/data/uploads/6c240c3f5fb5f53f140b4b7945e6870b91d2f944/pwn`
  - 主机侧手工探针已确认输出 `FMT_PROBE.0x...`
- 最新完整回归会话：
  - 标题：`上传样本执行位+PoC回归 v2`
  - 会话 ID：`51adbcdce3934527bdfc1b1fb6908e6e`
  - 会话结果：`completed`
- 关键动态证据已真实产出：
  - `dynamic-analysis` 的 `gdb_poc` 返回 `completed`
  - `gdb_poc.stdout` 中 `validated = true`
  - 命中函数：`vuln @ 0x401347`
  - 断点：`0x4013c2`
  - `x/s $rdi` 已确认 `FMT_PROBE.%p.%p.%p.%p\n`
  - `native_probe.probe_line` 已确认真实输出 `FMT_PROBE.0x...`
- 报告与导出链路已真实确认：
  - 会话 `final_report` 包含 `## 已验证 POC`
  - 会话 `final_report` 包含 `from pwn import *`
  - 会话 `final_report` 包含 `BINARY = '/home/tankuku/agent/data/uploads/6c240c3f5fb5f53f140b4b7945e6870b91d2f944/pwn'`
  - `GET /api/v1/audits/51adbcdce3934527bdfc1b1fb6908e6e/report?format=markdown&download=true` 返回 `200`
  - `GET /api/v1/audits/51adbcdce3934527bdfc1b1fb6908e6e/report?format=json&download=true` 返回 `200`
  - 两种导出正文都已确认包含：
    - `## 已验证 POC`
    - `from pwn import *`
    - 正确的上传样本宿主机路径
- 当前 `10000` 端口实例上的再验收：
  - 标题：`样本初始审计-PoC脚本回归`
  - 会话 ID：`5145a1c979af4fea8aa40039d77619d3`
  - 会话结果：`completed`
  - `dynamic-analysis` / `exploitability-review` 在最终远端总结阶段报错：`DeepSeek completion timed out after 120s`
  - 但两者的 `evidence` 已保留，且均包含 `gdb_poc=completed`
  - `final_report` 仍成功包含：
    - `## 已验证 POC`
    - `from pwn import *`
    - 正确的上传样本宿主机路径
  - 这说明“子代理总结超时时整场报告丢失 PoC”的问题已被证据保留机制兜住

### 增量进展（2026-05-04 11:41:30 UTC）

- 已按用户要求移除 DeepSeek 的硬超时：
  - `app/llm.py` 不再对 completion 使用 `asyncio.wait_for(...)`
  - `AsyncOpenAI` 客户端超时现设为 `None`
  - 子代理可继续长时间思考，只要上游未卡死，就不会在 120 秒处被平台主动打断
- 已按用户要求精简前端“实时链路与工具能力”区：
  - `frontend/index.html` 已移除“模型后端”“模型路由”和 WebSocket 状态说明
  - 当前仅展示“当前可调用工具”及其“可用 / 不可用”状态
  - `frontend/static/app.js` 的工具卡片已收敛为最小展示，不再铺开 family/mode/路径/说明
- 已按用户要求精简审计表单：
  - 已删除 `目标路径` 输入区
  - 已删除 `分析师笔记` 输入区
  - 已删除 `/bin/ls` 示例填充按钮
  - 创建会话现要求先上传样本，再使用 `artifact_id` 发起审计
- 已补充前端清理操作：
  - 会话列表工具栏新增 `清除选择`
  - 审计表单操作区新增 `清空表单`
  - 清空表单会一并清理当前已上传样本状态
- 已补充测试并保持基线稳定：
  - `tests/test_llm.py` 已改为验证“慢返回可正常完成”，不再断言 120 秒硬超时
  - `tests/test_frontend.py` 已改为验证首页不再显示旧的目标路径/分析师笔记/模型后端/模型路由文案，并已出现 `清空表单` / `清除选择`
  - 当前已验证：`./.venv/bin/pytest -q` 通过，结果为 `42 passed`
  - 当前已验证：`./.venv/bin/python -m compileall app tests` 通过

### 最新真实端到端验收（前端精简 + 无硬超时）

- 已重启 `10000` 端口服务到最新代码：
  - 当前监听进程：`uvicorn` on `0.0.0.0:10000`
  - `GET /api/v1/runtime` 仍返回：
    - `llm_backend=DeepSeekLLMBackend`
    - `llm_provider=deepseek`
    - `llm_status=ready`
    - `docker_runtime=true`
  - `GET /api/v1/progress` 仍返回 `404`
- 已直接校验首页 HTML：
  - 页面包含 `清空表单`
  - 页面包含 `清除选择`
  - 页面包含 `当前可调用工具`
  - 页面已不再包含：
    - `模型后端`
    - `模型路由`
    - `分析师笔记`
    - `/bin/ls 或项目内样本路径`
- 已直接校验当前 `/static/app.js`：
  - 已不再包含：
    - `loadDemoPayload`
    - `target-path`
    - `analyst-notes`
    - `state.runtimeProfile`
  - 已包含：
    - `resetAuditForm`
    - `clearSelectedSession`
- 已真实走通“仅上传样本 -> 使用 artifact_id 创建审计”的新前端主链路：
  - 新上传样本 `artifact_id`：`08904a898a3d4c339cf25312fa9606acf77627c4`
  - 新建会话 ID：`79db41ded6ac4199be01f2c6ed95f179`
  - 会话创建时无需 `target_path`，后端已正确回填落盘路径
- 已真实验证“无硬超时”生效：
  - 会话 `79db41ded6ac4199be01f2c6ed95f179` 在创建后超过旧的 `120s` 阈值仍保持有效运行
  - 超过 `180s` 后再次查询结果：
    - `triage = completed`
    - `static-analysis = completed`
    - `dynamic-analysis = running`
    - `has_timeout_error = false`
  - 当前未再出现旧版 `DeepSeek completion timed out after 120s`

### 增量进展（2026-05-04 12:55:00 UTC）

- 已完成前端信息架构重构并收口到多视图布局：
  - 左侧固定蓝白侧边栏：`首页 / 审计项目 / 审计项目任务管理 / 报告生成 / 知识库 / 系统设置`
  - 平台标题已统一为 `思而听二进制漏洞审计平台`
  - 首页已改为总览面板，不再把所有模块堆在同一页面
- 已完成首页新交互与可视化：
  - `新建审计任务` 改为弹窗上传流，先上传文件，再用 `artifact_id` 创建审计
  - 首页现展示 `待审计任务 / 审计中任务 / 已完成任务 / 已发现问题`
  - 首页现展示 `高危 / 中危 / 低危` 统计、饼图和问题趋势折线
  - 首页背景已加入代码主题 SVG 图层，保持蓝白配色
- 已完成任务管理与报告视图重构：
  - `审计项目任务管理` 现集中展示总体进度、子代理当前状态、agent 协作日志和运行时间线
  - 子代理进度现同时基于已落库 `evidence` 与运行中的 `tool_result` 事件计算，不再因为总结尚未结束而长期显示为低进度
  - `报告生成` 现只展示当前项目摘要、最终报告预览和导出入口
  - `系统设置` 现只展示系统状态与“当前可调用工具”的可用性，不再展示模型后端和模型路由
- 已完成前端噪音清理：
  - 删除旧的 `目标路径` 输入区
  - 删除旧的 `分析师笔记` 输入区
  - 顶栏保留 `清除当前项目`，避免残留选择干扰多项目切换
- 已补齐前端回归测试：
  - `tests/test_frontend.py` 现改为断言新版标题、导航、弹窗和清理后的用户文案
  - 当前已验证：`./.venv/bin/pytest -q` 通过，结果为 `42 passed`
  - 当前已验证：`node --check frontend/static/app.js` 通过

### 最新真实端到端验收（前端重构）

- 运行态复核：
  - `ss -ltnp` 已确认 `uvicorn` 监听 `0.0.0.0:10000`
  - `GET /api/v1/runtime` 返回：
    - `llm_backend=DeepSeekLLMBackend`
    - `llm_provider=deepseek`
    - `llm_status=ready`
    - `docker_runtime=true`
- 前端资源复核：
  - `GET /` 已确认输出新版标题 `思而听二进制漏洞审计平台`
  - 首页已确认包含：
    - `首页`
    - `审计项目`
    - `审计项目任务管理`
    - `报告生成`
    - `知识库`
    - `系统设置`
    - `新建审计任务`
    - `清除当前项目`
  - 首页已确认不再包含：
    - `在线二进制漏洞审计平台`
    - `分析师笔记`
    - `/bin/ls 或项目内样本路径`
    - `模型后端`
    - `模型路由`
  - `GET /static/app.js` 已确认服务端输出新版 bundle
- 新建任务主链路复核：
  - 已真实上传样本 `/home/tankuku/timu/pwn/attachment_2/pwn`
  - 新上传 `artifact_id`：`c8a23169b01513b2dbbb407d5a0e9429e890cd69`
  - 已真实创建会话：`81c6f58bd84e4ea19f6cd2c0b4483733`
  - 会话创建后状态进入 `running`，说明“弹窗上传 -> artifact -> create audit”链路可用
- 任务管理与报告数据源复核：
  - 已复核完成会话：`ead5b88a75eb41ae92caa4d055db32cd`
  - 会话标题：`2026-05-04 已验证PoC验收 v3 exploit-script`
  - 会话结果：`completed`
  - `4` 个 Docker 子代理均已回填 `container_id`
  - agent 协作计数已确认：
    - `agent_message_sent=33`
    - `agent_message_received=48`
  - 已确认任务管理页可直接消费：
    - 子代理状态
    - 工具调用结果
    - agent 协作事件
    - 进度时间线事件
- 报告导出与利用脚本复核：
  - `GET /api/v1/audits/ead5b88a75eb41ae92caa4d055db32cd/report?format=markdown&download=true` 返回 `200`
  - 响应头已确认返回附件文件名
  - 导出正文已确认包含：
    - `## 已验证 POC`
    - `已验证利用脚本`
    - `from pwn import *`
    - `FMT_PROBE`
    - 上传样本真实路径

### 当前观察

- 为验证新版弹窗链路而创建的会话 `81c6f58bd84e4ea19f6cd2c0b4483733` 当前仍处于长思考运行中，尚未回填首批子代理证据；这与当前“取消 LLM 硬超时”的运行策略一致。
- 本轮对前端布局的真实验收以线上 HTML/JS 输出、真实会话数据、导出报告和全量测试为主；暂未引入浏览器级截图自动化。
