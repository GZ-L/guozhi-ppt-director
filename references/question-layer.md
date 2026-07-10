# Question Layer

Use this file only to render unresolved decisions defined by `CALLING_SPEC.md`. It does not classify operations, define routes, or change state transitions.

## Human Mode

When material decisions are missing, show one complete recommendation:

```markdown
我建议按下面的配置制作，确认后开始生成：

- 页数/时长：[exact page count] 页，约 [minutes] 分钟
- 交付：[deliverable]
- 路线：[route_id and label]
- 风格：[style_id and style name]
- 内容处理：[rewrite boundary]
- 演讲备注：[yes/no]

推荐依据：[one evidence-based sentence]
已知风险：[one concrete risk or none]

请回复“确认推荐方案”，或只指出需要修改的字段。
```

Rules:

- Do not hide alternatives in a file while asking the user to choose them.
- Do not show unused alternatives before the user rejects the recommendation or asks to compare.
- If the user requests alternatives, label each field explicitly, for example `route_id: native_pptx` or `style_id: ref-16-black-ai-collaboration-editorial`.
- A confirmation applies only to the immediately preceding complete recommendation.
- If the user changes one field, preserve all other confirmed fields and present the updated complete configuration once.
- If all required fields were already explicit and the user authorized direct generation, record confirmation without another question.

## Agent Mode

Return a result conforming to `contracts/result.schema.json`:

```json
{
  "protocol_version": "1.0",
  "request_id": "request-123",
  "run_id": "run-123",
  "operation": "deck.create",
  "status": "needs_input",
  "resolved_decisions": {},
  "unresolved_fields": ["page_count", "style_id"],
  "proposed_decisions": {
    "page_count": 6,
    "style_id": "ref-16-black-ai-collaboration-editorial"
  },
  "artifacts": [],
  "warnings": [],
  "error": null,
  "next_action": "Parent Agent obtains confirmation or supplies authorized defaults."
}
```

The child Agent never asks the end user directly. The parent Agent resumes with the same `request_id` and `run_id`.

## Material Decisions

For deck production, unresolved means any missing or conflicting value among:

- exact page count;
- deliverable;
- route ID;
- style ID, `preserve_existing`, or confirmed DashiAI theme;
- rewrite boundary;
- speaker-notes decision.

Audience and occasion are required only when they materially affect story or style and cannot be derived from explicit source context. Record any derivation as proposed until confirmation.
