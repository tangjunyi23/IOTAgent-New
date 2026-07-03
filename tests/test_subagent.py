from app.subagent import SubAgentWorker
from app.observers import AgentObservationState
from app.models import SubAgentPayload, SubAgentTask


def test_extract_promoted_notes_prefers_core_conclusions():
    worker = object.__new__(SubAgentWorker)
    content = """
## 3. 利用性判断
1. 第一次溢出：控制返回地址并泄漏 libc 地址。
2. NX 开启，因此需要 ROP。

## 4. 值得提升为核心笔记的结论
1. 主漏洞：`sym.get_info` 中 `fgets(0x100)` 写入 `[rbp-0x40]` 的 `0x40` 字节栈缓冲区，溢出已证明存在。
2. 利用条件：`checksec` 证实 `No canary` 且 `No PIE`，返回地址控制可直接成立。
3. 后门线索：`sym.my_gadget` 零调用，适合作为固定地址 ROP 原语。
"""

    notes = worker._extract_promoted_notes(content)

    assert len(notes) == 3
    assert any("主漏洞" in note for note in notes)
    assert any("利用条件" in note for note in notes)
    assert all("第一次溢出" not in note for note in notes)


def test_extract_promoted_notes_still_accepts_keyword_bullets_outside_core_section():
    worker = object.__new__(SubAgentWorker)
    content = """
- 函数风险: `main` 将可控输入直接作为 `printf` 的格式字符串。
- 利用性判断: 已具备格式化字符串读写原语。
- 下一步建议: 继续泄漏 libc。
"""

    notes = worker._extract_promoted_notes(content)

    assert notes == [
        "函数风险: `main` 将可控输入直接作为 `printf` 的格式字符串。",
        "利用性判断: 已具备格式化字符串读写原语。",
    ]


def test_extract_promoted_notes_skips_section_heading_bullets():
    worker = object.__new__(SubAgentWorker)
    content = """
- 利用性判断
- 主漏洞：`main` 中存在格式化字符串漏洞。
"""

    notes = worker._extract_promoted_notes(content)

    assert notes == ["主漏洞：`main` 中存在格式化字符串漏洞。"]


def test_extract_promoted_notes_skips_conditional_action_lines():
    worker = object.__new__(SubAgentWorker)
    content = """
- 必要时通过动态输入（如 `AAAA%p.%p`）观察输出是否包含栈数据。
- 若 `printf` 的第一参数直接为 `buf`，则用户输入可控的格式化字符串漏洞成立。
- **结论：未知漏洞，未建立利用上下文。** 当前证据仅能说明一旦存在漏洞，利用难度因非 PIE 和 Partial RELRO 而有所降低，但尚不能论述更多。
- 现有证据已锁定输入路径，只要补全 `main` 的代码，即可立即对漏洞做出确定结论。
- **No PIE + No Canary**：若存在溢出，攻击者无需绕过 ASLR 和栈保护。
- 主漏洞：`main` 中存在格式化字符串漏洞。
"""

    notes = worker._extract_promoted_notes(content)

    assert notes == ["主漏洞：`main` 中存在格式化字符串漏洞。"]


def _make_payload(role: str, round_index: int, *, continue_role: bool = False) -> SubAgentPayload:
    return SubAgentPayload(
        session_id="sess-1",
        session_title="t",
        task=SubAgentTask(
            role=role,
            objective="o",
            model="m",
            target_path="/tmp/sample",
            round_index=round_index,
        ),
        core_notes=[],
        objective="o",
        target_path="/tmp/sample",
        continue_role_session=continue_role,
    )


def test_role_state_persists_across_rounds_and_clears_on_session_end():
    """Round N+1 with continue_role_session=True must reuse the cached state
    (preserving message history) instead of starting fresh."""
    worker = object.__new__(SubAgentWorker)
    worker._role_state_cache = {}

    # Round 1: build a fresh state, simulate an assistant turn recorded.
    payload_r1 = _make_payload("static-analysis", 1)
    state_r1 = AgentObservationState(
        agent_id="task-r1",
        role="static-analysis",
        system_prompt="sys",
        notes={},
    )
    state_r1.messages = [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "plan round 1"},
        {"role": "assistant", "content": "round-1-finding: gets overflow"},
    ]
    worker._role_state_cache[("sess-1", "static-analysis")] = state_r1

    # Round 2: continuation must merge into the SAME state, keep messages, and
    # append a round-boundary marker — NOT call reset_context.
    payload_r2 = _make_payload("static-analysis", 2, continue_role=True)
    cached = worker._role_state_cache.get(("sess-1", "static-analysis"))
    assert cached is not None
    worker._refresh_state_for_continuation(cached, payload_r2)

    # Prior assistant finding survives the round switch.
    assert any(m.get("content", "").startswith("round-1-finding") for m in cached.messages)
    # A round-boundary system message was appended.
    assert any("第 2 轮继续" in m.get("content", "") for m in cached.messages)
    # agent_id updated to the new round's task id.
    assert cached.agent_id == payload_r2.task.id

    # clear_role_state wipes the session's cached states.
    worker.clear_role_state("sess-1")
    assert ("sess-1", "static-analysis") not in worker._role_state_cache
