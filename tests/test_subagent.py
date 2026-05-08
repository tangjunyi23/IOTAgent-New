from app.subagent import SubAgentWorker


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
