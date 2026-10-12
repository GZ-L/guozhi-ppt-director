# Real Cases

这些案例来自 `guozhi-ppt-director` 的真实使用过程，用于说明调用协议和回归保护。经过验证并获得发布授权的 PPTX 与预览位于 [`examples/decks/`](decks/README.md)；案例不附带用户 PDF、第三方参考截图或未经验证的演示成品，也不把历史字母选项重新解释为当前稳定 ID。

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
  "protocol_version": "1.1",
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
  "verification": [],
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

## 案例五：可编辑 PPTX 与网页动效同时交付

用户确认保留可编辑 PPTX，并增加同内容的点击式网页动效。协议 `1.1` 使用路线 `dual` 和 profile `dual_motion_v1`，只维护一份故事、术语和语义揭示顺序，但分别记录两个制品的验证证据：

```json
{
  "protocol_version": "1.1",
  "request_id": "req-dual-motion-001",
  "operation": "deck.revise",
  "interaction_mode": "agent",
  "source": [{"type": "run", "location": "run-static-001", "role": "primary"}],
  "constraints": {
    "deliverable": "dual",
    "route_id": "dual",
    "revision_scope": "增加与现有内容一致的动效版本",
    "motion": {
      "requested": true,
      "profile_id": "dual_motion_v1",
      "playback_targets": ["browser", "powerpoint_365_macos"],
      "verification_required": "playback",
      "advance": "manual",
      "reduced_motion_fallback": true
    },
    "video": {"requested": false}
  },
  "confirmation": {"status": "confirmed", "exact_text": "确认动效版"}
}
```

HTML 的浏览器播放证据不能替代 PPTX 结构证据；任一制品失败时，结果必须指出具体制品和验证等级。

## 案例六：要求 PowerPoint 实播但本机没有 PowerPoint

用户要求 `pptx_basic_v1`，并明确 `verification_required: playback`、目标为 `powerpoint_365_macos`。`scripts/check_motion_capabilities.py` 检测到本机只有 Keynote，没有 Microsoft PowerPoint。

正确结果是：

```json
{
  "protocol_version": "1.1",
  "request_id": "req-pptx-playback-001",
  "run_id": "run-pptx-playback-001",
  "operation": "deck.create",
  "status": "blocked",
  "resolved_decisions": {
    "route_id": "native_pptx",
    "motion": {
      "requested": true,
      "profile_id": "pptx_basic_v1",
      "playback_targets": ["powerpoint_365_macos"],
      "verification_required": "playback"
    }
  },
  "unresolved_fields": [],
  "proposed_decisions": {},
  "artifacts": [],
  "verification": [],
  "warnings": [],
  "error": {
    "code": "MOTION_TARGET_UNAVAILABLE",
    "stage": "capability_check",
    "message": "Microsoft PowerPoint 365 for macOS is unavailable.",
    "evidence": "scripts/check_motion_capabilities.py report"
  },
  "next_action": "在安装 PowerPoint 365 的环境恢复同一 run，或重新确认 structural 验证等级"
}
```

Skill 不得用 Keynote 打开成功、OOXML 结构通过或 HTML 动效正常来冒充 PowerPoint 实播验证。

## 案例七：父 Agent 把渲染环节交给另一个 Skill

父 Agent 已经让导演 Skill 完成确认、故事和版式合同。渲染 Skill 只接收已冻结的导演上下文，不重新判断页数、风格或路线：

```json
{
  "protocol_version": "1.1",
  "request_id": "req-agent-render-001",
  "run_id": "run-agent-render-001",
  "capability_id": "render-native-pptx-001",
  "role": "renderer",
  "status": "requested",
  "producer": "presentations",
  "input": {
    "director_package": "outputs/ai-agent/run-agent-render-001/director-package",
    "output_path": "outputs/ai-agent/run-agent-render-001/artifacts/deck.pptx"
  },
  "output": {},
  "version": null,
  "director_context": {
    "route_id": "native_pptx",
    "page_count": 6,
    "style_lock": "ref-16-black-ai-collaboration-editorial",
    "story_digest": "六页说明 AI Agent 从单点工具到协作工作流的演进",
    "layout_contract_path": "outputs/ai-agent/run-agent-render-001/director-package/outline.md"
  },
  "error": null
}
```

调用前后都用 `scripts/validate_runtime_payload.py --kind handoff` 校验，并把请求与完成记录追加到 manifest 的 `capabilities`。渲染 Skill 若无法满足 `native_pptx` 或可编辑性要求，必须返回 `blocked` 或 `failed`，不能自行改用网页路线。
