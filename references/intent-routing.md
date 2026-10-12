# Intent Routing

Read this after `CALLING_SPEC.md` when the caller did not provide an explicit structured operation. Stable operation IDs and examples are defined in `contracts/intent-registry.json`.

## Classification Order

1. Use an explicit structured `operation` from the current invocation.
2. Detect explicit style-library mutation language such as “添加到风格库”, “更新这个风格 ID”, or “删除 ref-xx”.
3. Existing deck/run plus requested artifact changes maps to `deck.revise`.
4. A request for a new presentation artifact maps to `deck.create`.
5. Inspection with no mutation maps to `deck.review`.
6. Capability or usage explanation with no artifact work maps to `help`.

Context does not override explicit current language. “把这个加进去” is not enough to choose between `style.add` and `deck.revise`; return `needs_input` with one question.

## Mutation Boundary

- Using a reference for one deck never mutates the style library.
- `style.add`, `style.update`, and `style.remove` require explicit library intent and mutation approval.
- Reviewing a deck never creates or revises presentation artifacts.
- Asking how the Skill works never resumes an old deck run unless the caller supplies its `run_id` and a deck operation.

## Human And Agent Rendering

- Human mode asks one concise clarification only when multiple stable operations remain plausible.
- Agent mode returns `status: needs_input`, `unresolved_fields: ["operation"]`, the plausible operation IDs, and one `next_action`. It never asks the end user directly.
- Resume with the same `request_id`; do not create a new run until the operation is resolved.

## Non-Triggers

Do not invoke this Skill for a summary, translation, or general content rewrite when no presentation, style-library, presentation review, motion, video-deck, or presentation-output task is requested.
