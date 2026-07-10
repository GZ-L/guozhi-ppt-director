# Output Routes

Route identifiers are defined by `contracts/route-registry.json`. This file explains their use and cannot rename them.

## `native_pptx`

Use for editable PowerPoint delivery. The renderer must support editable text and shapes, preserve notes when requested, export a `.pptx`, and provide a render or open-file QA path.

If no native renderer is available, return `blocked`; do not silently change routes.

## `web_deck`

Use only when HTML presentation, motion, responsive scenes, screen recording, or interactive demonstration is explicitly required. Deliver the HTML project or preview path and run viewport/overlap checks.

## `dual`

Use only after explicit confirmation that both editable PPTX and web output are required. Produce both from one confirmed story, terminology set, style lock, and page-job map. QA each artifact separately.

## `dashiai`

Use only when DashiAI/template-engine output is explicitly requested or confirmed. Read `references/dashiai-adapter.md`, run `scripts/check_dashiai_adapter.py`, confirm theme and media intent, then render from the completed director package.

DashiAI remains an external renderer and template dependency. It does not own story, page count, style routing, or QA.

## `review_only`

Use for `deck.review`. Return evidence-based findings, suggested fixes, and optional revised planning material. Do not generate presentation artifacts unless a later invocation uses `deck.create` or `deck.revise`.

## Selection Rules

- Explicit structured `route_id` wins.
- Explicit user confirmation wins over a recommendation.
- Default to `native_pptx` only when defaults are authorized and PPTX is compatible with the requested deliverable.
- A request for beauty alone does not authorize a renderer change.
- Never infer a route from an unqualified letter or an option label from an earlier, unrelated turn.
