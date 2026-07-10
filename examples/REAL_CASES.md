# Real Cases

这些案例来自 `guozhi-ppt-director` 的真实使用过程，用于说明调用协议和回归保护。案例不附带用户 PDF、第三方截图或未经验证的演示成品，也不把历史字母选项重新解释为当前稳定 ID。

## 案例一：PDF 转 6 页可编辑 PPTX

真实请求先只提供了 `x-com-khazix0918-status-2074721296701849703.pdf` 并说“帮我做一套 PPT”，随后确认“做 6 页，可编辑 PPTX，带演讲备注”。

旧流程的问题是可能在第一次消息后直接生成，或者把历史字母选项当成永久路线。协议 `1.0` 的正确行为是：

1. 将 PDF 归一化为主来源。
2. 生成一个完整推荐，包括精确页数、`route_id`、`style_id`、改写边界和备注开关。
3. 在风格仍未锁定时返回 `needs_input`，不渲染。
4. 用户确认完整配置后，使用同一个 `request_id` 和 `run_id` 进入 `confirmed`。
5. 只有 PPTX 存在且通过可编辑性、备注和视觉 QA 后才返回 `completed`。

示意结果信封：

```json
{
  "protocol_version": "1.0",
  "request_id": "req-khazix-pdf",
  "run_id": "run-khazix-pdf-01",
  "operation": "deck.create",
  "status": "needs_input",
  "resolved_decisions": {
    "page_count": 6,
    "deliverable": "pptx",
    "route_id": "native_pptx",
    "speaker_notes": true
  },
  "unresolved_fields": ["style_id", "rewrite_boundary"],
  "proposed_decisions": {
    "style_id": "ref-16-black-ai-collaboration-editorial",
    "rewrite_boundary": "rebuild"
  },
  "artifacts": [],
  "warnings": [],
  "error": null,
  "next_action": "由父 Agent 或用户确认推荐的风格 ID 与改写边界"
}
```

这里的 `style_id` 是当前目录规则产生的示意推荐，不声称它等同于历史字母选项。

## 案例二：只展示一个方案却要求“确认 A/B/C”

真实交互中曾出现过：系统只展示一个方案，下一句话却要求用户回复“确认 A、B 或 C”。这使用户无法知道字母对应什么，也让 Agent 无法稳定恢复状态。

协议 `1.0` 的修复是：

- 默认只给出一个完整推荐，并用精确 `route_id` 和 `style_id` 表达。
- 用户说“确认推荐方案”时，只确认紧邻上一条消息中的完整配置。
- 只有用户主动要求比较方案时才展示多个方案，而且每个方案都必须完整列出稳定 ID。
- Agent 模式不展示对话菜单，只返回 `unresolved_fields`、`proposed_decisions` 和 `next_action`。

这个案例现在由 `tests/test_contract.py` 和 `scripts/validate_contract.py` 中的歧义标记检查保护，避免 `Route A:`、`确认 A/B/C` 等表达重新进入运行文档。

## 案例三：单张封面参考导致整套 PPT 僵硬

真实反馈指出：风格库过去只截封面或主题页，生成器会把封面构图机械扩散到每一页，导致页面缺少叙事连续性。

当前处理方式是把本地 PDF、图片文件夹或公开作品页整理为多页面角色风格包：

```text
cover -> section -> body -> process -> compare -> data -> closing
```

完整演示优先选择覆盖 4 至 8 张代表页面的风格包。只有一张图的条目标记为 `cover-only`；`limited` 风格必须由用户明确接受，不能作为完整演示的默认主参考。

这个改动不会复制来源内容。运行时先从角色覆盖中提取视觉语法，再为当前内容生成新的页面布局合同。

## 案例四：父 Agent 调用时缺少风格决策

父 Agent 已经确定来源、6 页、PPTX 和演讲备注，但没有获得用户的风格确认：

```json
{
  "protocol_version": "1.0",
  "request_id": "req-agent-042",
  "operation": "deck.create",
  "interaction_mode": "agent",
  "source": [
    {"type": "url", "location": "https://x.com/Saccc_c/status/2075553941270741235", "role": "primary"}
  ],
  "constraints": {
    "language": "zh-CN",
    "page_count": 6,
    "deliverable": "pptx",
    "route_id": "native_pptx",
    "style_id": null,
    "rewrite_boundary": "rebuild",
    "speaker_notes": true
  },
  "confirmation": {"status": "pending", "exact_text": null}
}
```

Skill 必须向父 Agent 返回 `needs_input`，而不是直接向最终用户发问，也不能自行选一个风格后开始渲染。父 Agent 可以把推荐呈现给用户，或者在获得 `allow_defaults` 授权后恢复同一个运行。
