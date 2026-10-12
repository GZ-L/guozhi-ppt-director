---
name: guozhi-ppt-director
description: Use when a user or Agent needs to create, revise, review, beautify, animate, or add video to a presentation from articles, PDFs, links, scripts, research, business material, or creator topics; manage the presentation style library; or coordinate PPTX, web-deck, PDF, video, motion, and DashiAI output. Do not use for one-off summaries that do not need a presentation workflow.
---

# Guozhi PPT Director

Direct presentation work from source material to a confirmed, style-locked, validated deliverable. This Skill owns classification, story, style, route, layout contracts, and QA; other capabilities act only as source adapters, media generators, renderers, or visual QA.

## Core Contract

- Read `CALLING_SPEC.md` first for every invocation.
- Read `MAINTENANCE_SPEC.md` before changing this Skill.
- Use stable operation, route, and state identifiers from `contracts/`; never infer meaning from an unqualified letter choice.
- In `agent` interaction mode, return the structured result envelope and never ask the end user directly.
- Stop with `needs_input` when a material decision is ambiguous or missing.
- Use one primary style-pack lock, `preserve_existing`, or one confirmed DashiAI theme. Do not invent an unreferenced hybrid.
- Treat single-image references as `cover-only`; use `limited` packs only after explicit acceptance.
- For visual intent and generated media, the PPT style lock is authoritative, and the template media treatment is authoritative for dimensionality, material, lighting, depth, photography, CGI, or illustration rendering. Build and validate `media-plan.json`; external image or IP capabilities may supply image form under `visual_intent_only` but never changes the deck style or replaces template image treatment. Every generated slot uses `inherit_ppt_style`.
- When a library style is unresolved, return `style_candidates`: three eligible style candidates containing one recommended candidate and two visual alternatives. Every candidate includes its stable ID, name, style category, visual traits, fit evidence, and visible Preview asset; `recommended_style_id` identifies the recommendation. Selection is deterministic and never random. Never ask a user to confirm a bare style ID or letter.
- Treat motion and video as explicit capabilities. Confirm a profile, playback targets, media policy, and `verification_required`; never describe a static artifact as animated.
- Treat a general motion request as in-slide choreography, not only page transitions. Build `motion-plan.json`, group semantic visual units, use automatic sequences inside explanations, and keep clicks for semantic checkpoints. Dynamic card/image requests use visible entrance variety, stable object names resolved against the exported PPTX, and content-bearing visuals instead of generic filler. Transition-only output requires an explicit transition-only request.
- Require one readable full-size slide preview per page. A montage is navigation only; it cannot prove layout quality. When object-level layout JSON exists, declare top-level surface groups and pass collision verification before `completed`.
- Never copy reference text, logos, brands, people, characters, exact artwork, claims, or exact page composition.

## Workflow

1. Classify one stable operation from `CALLING_SPEC.md`.
2. Create or load `templates/run-manifest.json` and normalize sources and constraints.
3. Check required fields, renderer capabilities, and style eligibility.
4. Recommend one complete configuration plus the validated three-style candidate set, or return structured `needs_input`.
5. Freeze confirmed decisions, then build the brief, outline, style lock, layout contracts, `media-plan.json`, and production route.
6. Validate media intent and any capability handoff before generating assets or rendering.
7. Render through the confirmed adapter only after state `confirmed` and `planned`.
8. QA requested artifacts and return `completed`, `blocked`, or `failed` with evidence.

## Resource Routing

- `CALLING_SPEC.md`: runtime operations, identifiers, precedence, state machine, call order, coordination, and result contract.
- `MAINTENANCE_SPEC.md`: change ownership, synchronization, compatibility, and release validation.
- `contracts/`: machine-readable intent, route, invocation, run-manifest, handoff, and result contracts.
- `contracts/intent-registry.json`: operation intent examples, precedence, ambiguity, and non-trigger cases.
- `contracts/capability-handoff.schema.json`: parent Agent to capability provider request/response contract.
- `contracts/style-selection.schema.json`: deterministic three-candidate style recommendation contract.
- `contracts/media-plan.schema.json`: visual-intent, source-priority, style-sovereignty, editability, and optional-character contract.
- `OVERVIEW.md`: concise capability and architecture map.
- `README.md`: installation, public usage, examples, validation, and publication boundaries.
- `NOTICE.md`: ownership, third-party reference, and external-renderer boundaries.
- `examples/REAL_CASES.md`: real interaction and regression cases for users and Agent integrators.
- `references/question-layer.md`: human and Agent confirmation rendering.
- `references/intent-routing.md`: natural-language operation classification and ambiguity handling.
- `references/style-routing.md`: style selection and fidelity gate.
- `references/style-library/README.md`: style-library add, update, and collection procedures.
- `references/style-library/style-match-rules.md`: deterministic eligibility, scoring, and tie-break rules.
- `references/style-library/zcool-style-catalog.md`: built-in reference catalog.
- `references/layout-contracting.md`: page roles, skeletons, text budgets, and media slots.
- `references/output-routes.md`: stable route definitions.
- `references/motion-video-delivery.md`: motion profiles, video policy, capability gates, and verification levels.
- `references/visual-intent-analysis.md`: article-to-visual reasoning and media-slot decision rules.
- `references/xiaohu-ip-studio-adapter.md`: optional Xiaohu visual-analysis and media-generation adapter boundary.
- `references/dashiai-adapter.md`: external DashiAI renderer contract for route `dashiai`.
- `references/director-production-contract.md`: renderer boundary and output requirements.
- `references/qa-checklist.md`: story, visual, route, state, and delivery checks.
- `templates/`: run-manifest source plus human-readable run-package views.
- `templates/style-selection.json`: valid `style_candidates` example with `recommended_style_id` and Preview asset fields.
- `scripts/check_dashiai_adapter.py`: external DashiAI capability check.
- `scripts/check_motion_capabilities.py`: motion/video environment and playback-target capability check.
- `scripts/resolve_pptx_motion_shape_ids.py`: resolve stable object names to final exported PPTX Shape IDs before motion writing, especially for pictures and media.
- `scripts/apply_pptx_basic_motion.py`: restricted structural writer for fade transitions and supported appear/fade/wipe/slide entrance builds on clean PPTX slides.
- `scripts/verify_pptx_motion.py`: read-only PPTX transition, timing-target, and video-package verification.
- `scripts/verify_video_asset.py`: local video codec, duration, dimensions, audio, and checksum verification.
- `scripts/verify_web_motion.mjs`: Playwright browser verification for the `web_motion_v1` QA bridge, reveal sequence, reduced-motion mode, and video playback.
- `scripts/verify_slide_previews.py`: per-slide PNG presence and minimum-resolution gate; rejects thumbnail-only QA.
- `scripts/verify_slide_collisions.py`: deterministic collision gate for declared top-level surfaces in object-level slide layout JSON.
- `templates/collision-rules.json`: run-specific surface-group rule template for collision verification.
- `templates/motion-plan.json`: run-specific `in_slide_grouped_v1` execution plan for card, diagram, product-part, and conclusion reveals.
- `templates/media-plan.json`: run-specific visual intent and generated-media plan.
- `templates/media-capability-handoff.json`: parent/child media request template with plan binding, generation scope, and confirmation context.
- `scripts/validate_contract.py`: protocol, reference, style-asset, and portability validation.
- `scripts/validate_runtime_payload.py`: invocation normalization plus invocation, run-manifest, result, capability-handoff, style-selection, and media-plan business-rule validation.

Published source checkouts contain style metadata but intentionally exclude third-party bitmap references. A missing local style asset makes that style ineligible at runtime; it never authorizes an unreferenced visual guess. Use `python3 scripts/validate_contract.py --require-style-assets` when validating a local installation that is expected to contain the complete authorized asset set.

## Validation

After changing the Skill, run:

```bash
python3 scripts/validate_contract.py
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 "$HOME/.codex/skills/standard-skill-maker/scripts/validate_skill.py" .
python3 "$HOME/.codex/skills/.system/skill-creator/scripts/quick_validate.py" .
```
