# Output Routes

Route identifiers are defined by `contracts/route-registry.json`. This file explains their use and cannot rename them.

## `native_pptx`

Use for editable PowerPoint delivery. The renderer must support editable text and shapes, preserve notes when requested, export a `.pptx`, and provide a render or open-file QA path.

Motion profile `pptx_basic_v1` is allowed only after `scripts/check_motion_capabilities.py` confirms the required verification level. It covers fade slide transitions and ordered appear, fade, directional wipe, and directional slide entrance builds, including `in_slide_grouped_v1` plans that reveal each semantic card, image, or diagram group as one unit; it does not cover arbitrary effects. A renderer may write those structures directly; otherwise export a clean PPTX, resolve stable object names with `scripts/resolve_pptx_motion_shape_ids.py`, use `scripts/apply_pptx_basic_motion.py`, and write a distinct output file. Run `scripts/verify_pptx_motion.py` for structural evidence. Embedded or linked video requires an explicit video policy and valid package relationships.

If no native renderer is available, return `blocked`; do not silently change routes.

## `web_deck`

Use only when HTML presentation, motion, responsive scenes, screen recording, or interactive demonstration is explicitly required. Deliver the HTML project or preview path and run viewport/overlap checks.

Use motion profile `web_motion_v1` for browser motion and video. Playback QA must exercise the declared initial, intermediate, and final states rather than checking only a static screenshot.

## `dual`

Use only after explicit confirmation that both editable PPTX and web output are required. Produce both from one confirmed story, terminology set, style lock, and page-job map. QA each artifact separately.

Use `dual_motion_v1` when both artifacts carry motion. Preserve one semantic reveal order, but record structural/playback evidence separately for PPTX and HTML.

## `dashiai`

Use only when DashiAI/template-engine output is explicitly requested or confirmed. Read `references/dashiai-adapter.md`, run `scripts/check_dashiai_adapter.py`, confirm theme and media intent, then render from the completed director package.

DashiAI remains an external renderer and template dependency. It does not own story, page count, style routing, or QA.

The current registered DashiAI capability is motion profile `none` and no video delivery. Do not infer animation from an HTML export without adapter evidence and a future registry update.

## `review_only`

Use for `deck.review`. Return evidence-based findings, suggested fixes, and optional revised planning material. Do not generate presentation artifacts unless a later invocation uses `deck.create` or `deck.revise`.

## Selection Rules

- Explicit structured `route_id` wins.
- Explicit user confirmation wins over a recommendation.
- Default to `native_pptx` only when defaults are authorized and PPTX is compatible with the requested deliverable.
- A request for beauty alone does not authorize a renderer change.
- Never infer a route from an unqualified letter or an option label from an earlier, unrelated turn.
