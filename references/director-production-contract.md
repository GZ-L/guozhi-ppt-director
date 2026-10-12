# Director Production Contract

Use this file after the user confirmation, outline, style match, style board, and production route are ready.

## Single-Director Rule

`guozhi-ppt-director` owns all presentation decisions:

- content structure
- page count and slide jobs
- style selection, style lock, and fidelity target
- production route
- QA standard
- delivery summary

Do not call another PPT Skill as a second director. A local renderer, PowerPoint operation, or code library may be used only as a mechanical production step after this Skill has produced the confirmed package.

## Required Production Package

Before final generation, collect:

- `user-confirmation.md`
- `deck-brief.md`
- `outline.md`
- `style-match.md` when style references are used
- `style-board.md`
- validated `media-plan.json` when any media slot is declared
- `production-route.md`
- `motion-plan.json` when motion is requested
- source files and citation notes

## Renderer Instructions

For editable PPTX:

- Use editable text, shapes, tables, charts, and image placeholders where possible.
- Avoid image-only slides unless the source itself is an image and editability is impossible.
- Keep speaker notes and source notes when relevant.
- Render or open the file for visual QA when tooling is available.
- Render one full-size slide preview per page, validate count and dimensions with `scripts/verify_slide_previews.py`, and inspect every page at readable scale. Montage is navigation only.
- When the renderer exposes object-level layout JSON, name top-level surfaces, declare cross-group rules from `templates/collision-rules.json`, and pass `scripts/verify_slide_collisions.py` before delivery.
- If Style Library Replica is selected, build against the primary style pack lock when available. Match the reference's palette, typography mood, spacing, layout rhythm, shape treatment, and density before adding any decorative ideas. Do not invent a hybrid style.
- If a primary style pack is selected, map each output slide to the closest pack role before building. Do not make every body page imitate the pack's cover page.
- Before creating slide objects, write a lightweight layout contract for every slide. Preserve the chosen skeleton and text/media budgets during rendering; shorten copy before shrinking type or adding extra boxes.
- When the user asks for pictures or a livelier deck, plan two to four content-bearing media slots across a short deck. Prefer authorized source screenshots, charts, illustrations, or product visuals; do not use generic filler. Keep each visual readable and preserve editable titles, captions, conclusions, and surrounding card geometry.
- Read `references/visual-intent-analysis.md` and validate `media-plan.json` before calling a media generator. The PPT style lock and template media treatment are authoritative: record real style-pack image references and use `inherit_ppt_style` for every generated or transformed visual. External visual analysis is `visual_intent_only`; it may influence the depicted subject, relationship, or pose but may not import its original hand-drawn skin, palette, line work, material, lighting, texture, typography, or page style.
- Do not copy external template engines, AGPL-licensed theme files, or third-party template assets into this Skill unless the user explicitly approves that integration. Use external systems as method references only.
- For `pptx_basic_v1`, render only confirmed fade transitions and supported appear/fade/wipe/slide entrance builds. For general animation requests, create in-slide choreography from `templates/motion-plan.json`, use three to five semantic beats per content slide, group each card or image with its frame/caption, use at least two visible entrance families across the deck, sequence explanations automatically, and reserve clicks for semantic checkpoints. Transition-only and all-fade delivery are insufficient for dynamic card or image requests unless explicitly constrained. Run `scripts/check_motion_capabilities.py` before rendering. Export the clean PPTX, run `scripts/resolve_pptx_motion_shape_ids.py` against stable object names, then use `scripts/apply_pptx_basic_motion.py` only when the renderer lacks those structures and the selected slides have no existing timing tree. Run `scripts/verify_pptx_motion.py` after export.
- Do not mark playback verification complete from OOXML inspection. Missing Microsoft PowerPoint for `verification_required: playback` is `MOTION_TARGET_UNAVAILABLE` and status `blocked`.
- For profile `none`, disclose `Static PPTX, no animation`; never let a static preview imply motion playback.

For visual web deck:

- Build previewable slides with stable dimensions.
- Verify that text is not overlapping or off-frame using full-size slide previews and available object-level collision data.
- Keep motion purposeful: reveal structure, sequence, or contrast.
- For `web_motion_v1`, expose stable scene/build/media IDs plus `window.__GUOZHI_DECK_QA__`, then run `scripts/verify_web_motion.mjs` to verify initial, intermediate, final, reduced-motion, and requested video-playback states.
- Export images, PDF, or video only when requested.
- If Style Library Replica is selected, compare screenshots against the primary reference during QA and revise any obvious drift.

For dual version:

- Keep one shared outline and terminology.
- QA each version separately.
- Do not let the visual version drift away from the editable version's facts.
- For `dual_motion_v1`, preserve one semantic reveal order and record independent evidence for each artifact.

For video:

- Resolve a playable local asset or confirmed external link before rendering.
- Run `scripts/verify_video_asset.py` for local media and record codec, duration, dimensions, audio streams, and checksum.
- Record delivery, playback, audio, loop, poster, fallback, slide/page, geometry, and source evidence.
- Validate embedded PPTX media relationships or browser playback events as appropriate.
- Treat exported MP4/MOV as a separate artifact with media-level QA.

For route `dashiai`:

- Read `references/dashiai-adapter.md`.
- Confirm route `dashiai`, DashiAI theme, output format, and media intent before rendering.
- Use DashiAI only after the director package, outline, style/theme decision, and layout contracts are complete.
- Convert the director package into DashiAI `goal.json`; every final slide must use concrete `layout + props`.
- Run DashiAI contract and output checks, including goal spec, copy/default text, media-slot, and rendered preview checks.
- Record DashiAI project path, selected theme, goal path, validation output, HTML preview, and exported files in `production-route.md` and `qa-report.md`.
- If DashiAI is unavailable, return `blocked` and request approval before changing routes.

## Fallback

If the environment cannot create the requested file, deliver the complete director package and state exactly which production capability is missing. Do not claim a final deck exists unless the file exists and has been checked.
