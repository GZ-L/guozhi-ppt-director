# Guozhi PPT Director Calling Spec

Protocol version: `1.1`

Invocation protocol `1.0` remains accepted for static compatibility and normalizes to a `1.1` run with motion profile `none`. It never authorizes inferred motion or video.

This is the runtime authority for every `guozhi-ppt-director` invocation. Read it before lower-level references, templates, style catalogs, or renderer instructions. `MAINTENANCE_SPEC.md` governs changes to the Skill; it does not govern a deck run.

## Authority And Failure Rule

1. Follow system, developer, and explicit user instructions.
2. Follow this protocol for classification, state, order, and coordination.
3. Use `contracts/route-registry.json` for route identifiers and the request/result schemas for machine fields.
4. Treat lower-level files as implementation guidance. They cannot redefine an operation, route, state, or transition.
5. When input is ambiguous, return `needs_input`. Never guess and continue to rendering.
6. Never modify this installed Skill during a deck production run. Contract drift is a maintenance task.

## Stable Operations

Use exactly one operation per invocation:

| Operation | Purpose | Mutates Presentation Files | Mutates Style Library |
| --- | --- | --- | --- |
| `deck.create` | Create a new deck from source material | yes | no |
| `deck.revise` | Revise an existing deck or run package | yes | no |
| `deck.review` | Review a deck, outline, style, or workflow | no | no |
| `style.list` | List or inspect available references | no | no |
| `style.add` | Add a new style reference or pack | no | yes |
| `style.update` | Refresh metadata, roles, or assets for an existing style | no | yes |
| `style.remove` | Remove a named style reference or pack | no | yes |
| `help` | Explain capabilities and usage | no | no |

Natural-language classification follows `contracts/intent-registry.json` and `references/intent-routing.md`. The stable operation identifier is the source of truth after classification. If two operations are plausible, return `needs_input` with one clarifying question; never choose from conversation momentum alone.

## Stable Routes

Use only route identifiers from `contracts/route-registry.json`:

- `native_pptx`
- `web_deck`
- `dual`
- `dashiai`
- `review_only`

User-facing labels may be translated, but never use an unqualified letter as a route identifier. A phrase such as “确认推荐方案” confirms only the single fully specified recommendation in the immediately preceding response.

## Interaction Modes

Every invocation has an `interaction_mode`:

- `human`: communicate with the end user. Recommend one complete configuration and ask only unresolved material questions.
- `agent`: return the structured result envelope to the caller. Do not ask the end user directly and do not present a conversational menu.

An Agent caller may provide already confirmed decisions. When all required fields are present and `confirmation.status` is `confirmed`, continue without another confirmation turn.

## Input Precedence

Resolve every field in this order:

1. Structured fields in the current invocation.
2. Exact decisions in the latest explicit user confirmation.
3. Confirmed values in the referenced `run-manifest.json`.
4. Deterministic defaults, only when `allow_defaults` is `true` or the user explicitly asked to proceed with defaults.
5. Proposed inference, recorded as unconfirmed and never treated as a decision.

Conflicting values at the same or higher level produce `needs_input`. Never silently merge page count, route, style, or deliverable conflicts.

## Required Inputs

| Operation | Required Before Work | Required Before Mutation Or Rendering |
| --- | --- | --- |
| `deck.create` | at least one source item | exact page count, deliverable, route, style lock, rewrite boundary, notes decision, motion/video decisions when requested, confirmation |
| `deck.revise` | existing deck path or `run_id`; requested revision scope | confirmed revision scope and any changed route/style/motion/video decisions |
| `deck.review` | deck, package, outline, or source to review | none |
| `style.list` | optional filter | none |
| `style.add` | source reference | generated or confirmed stable style ID and mutation approval |
| `style.update` | existing style ID and replacement/refresh source | mutation approval |
| `style.remove` | existing style ID | explicit destructive confirmation |
| `help` | none | none |

If speaking time is supplied without page count, propose an exact page count before confirmation. A range is not executable and cannot become a confirmed page count.

## Source Normalization

For deck operations, normalize each input into a source record before story planning:

```text
source_id, type, path_or_url, availability, extraction_method,
title, author, date, facts, citations, media, limitations
```

Use available PDF, browser, document, image, or repository capabilities only as source adapters. Record extraction failures and preserve source attribution. Source adapters do not decide story, style, route, or page count.

## State Machine

Allowed run states:

```text
received -> normalized -> needs_input -> confirmed -> planned
planned -> rendering -> qa -> completed
received|normalized|needs_input|confirmed|planned|rendering|qa -> blocked
received|normalized|confirmed|planned|rendering|qa -> failed
```

Rules:

- Append every accepted transition to `state_history`; never rewrite or skip earlier states.
- Validate `run-manifest.json` with `scripts/validate_runtime_payload.py --kind manifest` before promoting it to the next state.
- `needs_input` is resumable and must include unresolved fields plus one recommended resolution.
- `confirmed` requires an exact route ID, exact page count, deliverable, style decision, rewrite boundary, and notes decision for deck production.
- Rendering is forbidden before `confirmed` and `planned`.
- `blocked` means a required external capability or approval is unavailable; include a concrete next action.
- `failed` means execution was attempted and did not complete; include the failed stage and evidence.
- `completed` requires requested artifacts to exist, one full-size slide preview per page to pass resolution validation, and QA evidence to be recorded. A montage is navigation only and is never sufficient visual QA evidence.

## Deck Call Order

For `deck.create` and `deck.revise`, follow this order exactly:

1. Classify exactly one operation from the intent registry, create or load `run-manifest.json`, and assign `request_id`, `run_id`, operation, and `interaction_mode`.
2. Normalize source material and explicit constraints.
3. Run `scripts/validate_runtime_payload.py --kind invocation` on the normalized request. Record its normalized protocol `1.1` payload, required fields, and route/style/motion/video conflicts. If it returns unresolved fields, set `needs_input` and stop.
4. Build a provisional brief and estimate the page roles needed. Also build a provisional visual-needs summary using `references/visual-intent-analysis.md`: identify reader blocks, likely source assets, image form, generated-visual fallback, and any optional character proposal. This summary does not choose a second visual style.
5. Check renderer availability for the requested deliverable. When motion or video is requested, run `scripts/check_motion_capabilities.py` and verify that the route supports the confirmed profile and media delivery.
6. Score eligible style references, build `style_candidates` with three eligible style candidates, one recommended candidate, and two visual alternatives, then validate it with `scripts/validate_runtime_payload.py --kind style_selection`. Record `recommended_style_id`, fit evidence, visual family, and Preview asset for every candidate. Selection is deterministic and never random.
7. If a material decision is unresolved, set `needs_input` and stop. Optional IP or custom-character use is unresolved until the exact character/form is shown in the selected PPT visual language and confirmed. A low-cost baseline preview may be produced while the run remains `needs_input`; deck rendering remains forbidden.
8. Freeze confirmed decisions in the manifest.
9. Build the final brief, outline, style lock, layout contracts, production route, and `motion-plan.json` when motion is requested. Build `media-plan.json` from `templates/media-plan.json`, set every slot to `style_transform: inherit_ppt_style`, record real `media_treatment_references` from the confirmed style pack, and validate it with `scripts/validate_runtime_payload.py --kind media_plan` before any `media_generator` handoff. The PPT style lock is the only deck-style authority, and the template media treatment is authoritative for dimensionality, material, lighting, depth, photography, CGI, or illustration rendering. Image form may explain the content but may not alter those treatments. If source or template assets do not supply the needed subject, an external visual-analysis capability may choose what to depict under `fallback_image_form_policy: visual_intent_only`; it still renders with the template treatment. In-slide choreography must define a motion job, semantic order, grouped builds, stable object names, final object IDs, trigger, effect, and duration for every animated group. A general animation request normally uses three to five semantic beats per content slide, at least two visible entrance families across the deck, automatic `after_previous` sequences inside an explanation, and `on_click` only for semantic checkpoints. Transition-only and all-fade choreography are insufficient for dynamic card or image requests unless the confirmed target or reduced-motion policy requires them. When the user requests richer visuals, assign content-bearing media slots and prefer authorized source images over generic decoration.
10. Render through the selected adapter into a temporary or run-specific output directory. Produce one full-size slide preview per page at the final slide aspect ratio and at least 1280x720 for 16:9 decks. When the native renderer cannot write the confirmed `pptx_basic_v1` structures itself, export a clean PPTX, resolve named objects against the final package with `scripts/resolve_pptx_motion_shape_ids.py`, then use `scripts/apply_pptx_basic_motion.py` only on slides without an existing timing tree and write a new PPTX artifact. Pre-export layout IDs are never authoritative for pictures or media.
11. Run story, style, route, editability, source, rendered-output, and requested motion/video QA. Run `scripts/verify_slide_previews.py` and inspect every full-size slide preview at readable scale; a montage is navigation only. When the renderer exposes object-level layout JSON, create run-specific surface groups from `templates/collision-rules.json` and run `scripts/verify_slide_collisions.py`; a failed or missing declared collision verification blocks `completed`. For `pptx_basic_v1`, run `scripts/verify_pptx_motion.py`. For `web_motion_v1`, expose the QA bridge and run `scripts/verify_web_motion.mjs`. Playback claims require target-runtime evidence.
12. Promote checked artifacts, set `completed`, and return the result envelope.

## Review Call Order

For `deck.review`:

1. Normalize the supplied deck, package, outline, or source.
2. Confirm the requested review scope only when it is ambiguous.
3. Inspect story, source fidelity, style consistency, layout, density, route fit, editability, and rendered output when available.
4. Return findings ordered by severity with file/page evidence and unverified areas.
5. Do not create or revise presentation artifacts inside the review operation.

## Style-Library Call Order

- `style.list`: load indexes, apply any explicit filter, verify referenced assets, and return stable IDs plus coverage and status.
- `style.add`: verify mutation approval, normalize the source, generate a stable unused ID, collect representative roles, write pack metadata and assets, update indexes/catalog/contact sheet, then validate.
- `style.update`: verify mutation approval and existing ID, preserve ID meaning, update only requested metadata or assets, synchronize dependent files, then validate.
- `style.remove`: require explicit destructive confirmation naming the exact ID, remove only that entry and its owned assets, synchronize indexes/catalog/contact sheet, then validate.

If the installed Skill directory is not writable, mutation operations return `blocked`; they do not redirect output silently.

## Help Call Order

For `help`, answer from `SKILL.md`, this protocol, and `OVERVIEW.md`. Explain stable operation and route identifiers. Do not create run artifacts.

## Confirmation Behavior

In `human` mode:

- Lead with one recommended complete production configuration. When its library style is unresolved, show its validated `style_candidates`: one recommended candidate plus two visual alternatives.
- State known parameters and ask only for unresolved material decisions.
- Use exact identifiers for route and style.
- Render all three candidates with a human-readable name, style category, three to five visual traits, fit evidence, and Preview asset. Display every preview inline when the channel supports images.
- Never ask the user to confirm a bare `style_id` or letter. Ask for the exact style ID or exact style name shown with the preview.
- A candidate without a readable preview is ineligible. If fewer than three complete candidates remain, return `needs_input` and request an authorized reference instead of padding the set with a weak or random option.
- If the user supplied all decisions and explicitly said to proceed, record confirmation and continue.

In `agent` mode:

- Return `status: needs_input`, `unresolved_fields`, `proposed_decisions`, and `next_action`.
- Put the validated `style_candidates` object and `recommended_style_id` under `proposed_decisions` so the parent Agent can render the same three previews and recommendation evidence.
- The parent Agent decides whether to obtain user input or apply authorized defaults.
- Resume with the same `request_id` and `run_id`; do not create a second run for the same confirmation cycle.

## Style Decision

Visual production requires one of these explicit decisions:

- a confirmed style-pack ID from the library;
- `preserve_existing` for a revision that keeps the existing visual system;
- a confirmed DashiAI theme when route `dashiai` is selected.

When a library style remains unresolved, score references using `references/style-library/style-match-rules.md`, serialize the candidate set with `contracts/style-selection.schema.json`, and validate it before presentation. The highest deterministic effective score is `recommended_style_id`; the other two candidates must use distinct visual families. A `limited` reference is eligible only when the caller explicitly allows limited coverage. If three eligible candidates with readable previews cannot be produced, return `needs_input` and request a new reference. Explicitly confirmed styles, `preserve_existing`, and DashiAI themes do not require a new three-candidate comparison.

## Motion And Video Decision

Read `references/motion-video-delivery.md` whenever the request mentions animation, motion, dynamic presentation, video playback, screen recording, or video export.

- Use only profile IDs `none`, `web_motion_v1`, `pptx_basic_v1`, and `dual_motion_v1`.
- Motion requests require `profile_id`, one or more `playback_targets`, `verification_required`, `advance`, and reduced-motion fallback before confirmation. `dual_motion_v1` records both browser and PowerPoint targets when both artifacts require playback evidence.
- A general request for animation or motion includes in-slide choreography by default. Use `choreography_mode: in_slide_grouped_v1` for native PPTX and create the run-specific plan from `templates/motion-plan.json`. Group every card, diagram stage, label set, or conclusion that must enter as one visual unit. A page transition alone does not satisfy this request.
- Use `after_previous` for concise automatic sequences and `on_click` only at semantic checkpoints where the speaker must control progression. Each motion group records `group_id`, intent, stable `shape_names`, resolved final `shape_ids`, effect, trigger, and duration. Run `scripts/resolve_pptx_motion_shape_ids.py` after the clean PPTX export and before motion writing.
- Video requests require delivery, playback, audio, loop, poster-frame, fallback policy, and at least one normalized video asset before confirmation.
- The selected route must declare the profile and video delivery in `contracts/route-registry.json`. Resolve local media and run `scripts/verify_video_asset.py` before handing it to a renderer.
- `verification_required: playback` returns `blocked` with `MOTION_TARGET_UNAVAILABLE` when the declared runtime is missing. Structural inspection is not a silent substitute.
- Unsupported effects or media behavior return `needs_input` with one supported recommendation. Do not approximate them without confirmation.
- Human delivery for profile `none` must say `Static PPTX, no animation`. For any motion profile, state the exact profile, structural verification result, playback verification result, and unavailable target runtime. A preview image or montage never proves animation playback.

## Skill And Agent Coordination

`guozhi-ppt-director` is the only director. It owns request classification, story, page jobs, route, style lock, layout contracts, and QA.

Other Skills, tools, or Agents may fill one declared capability role:

- `source_adapter`: extract text, facts, citations, screenshots, or media;
- `media_generator`: create confirmed visual assets for declared media slots;
- `renderer`: convert the confirmed director package into PPTX, HTML, PDF, or images;
- `visual_qa`: inspect rendered pages for overlap, clipping, blank output, or style drift.

Minimum handoff payloads are stable:

| Role | Required `input` | Required `output` when completed |
| --- | --- | --- |
| `source_adapter` | `sources` | `source_records` |
| `media_generator` | `media_slots`, `generation_scope`; context path, digest, confirmation | one proved asset per requested slot |
| `renderer` | `director_package`, `output_path` | `artifacts` |
| `visual_qa` | `artifacts` | `findings`, `passed` |

Coordination rules:

1. Pass only the fields needed for that capability role.
2. Do not delegate confirmation, style choice, page count, or story ownership.
3. For `media_generator`, validate `media-plan.json` first. Bind the handoff to the exact file with `media_plan_path`, `media_plan_digest`, matching `request_id`, `run_id`, and `style_lock`. The adapter receives image form, must-show facts, target slot geometry, source priority, and the confirmed PPT style lock. It never receives authority to choose an independent skin; returned visuals must use `inherit_ppt_style` and never change the deck style.
4. Set `generation_scope` to `baseline_preview` for exactly one low-cost proposal asset while `confirmation_status` may remain `pending`. Set it to `production_assets` only when `confirmation_status` is `confirmed` or `defaults_authorized`. A child capability cannot widen this scope.
5. A completed media handoff returns one asset per requested slot. Each asset proves `slot_id`, source type, `ppt_style_lock`, `inherit_ppt_style`, `editable_ppt_text`, provenance, location, and `verified: true`. Missing or mismatched asset proof is rejected before renderer input.
6. Serialize every request and response with `contracts/capability-handoff.schema.json`; validate it with `scripts/validate_runtime_payload.py --kind handoff`. Use `templates/media-capability-handoff.json` for media calls. Record the validated handoff under manifest `capabilities`.
7. Every recorded handoff must use the same `request_id` and `run_id` as its manifest. A `production_assets` handoff is valid only when the manifest is `confirmed` or later and its confirmation is authorized.
8. Validate returned artifacts before using them downstream.
9. Never silently switch renderer or route. Set `blocked` or return `needs_input` for approval.

Standalone execution and parent-Agent execution use the same contracts. A Skill is declarative: the host Agent executes tool and child-Skill calls. As a standalone Skill, its host Agent follows `guozhi-ppt-director` to discover providers by capability role and perform the handoffs. Under a parent Agent, the parent invokes this Skill with `interaction_mode: agent`; this Skill returns `needs_input`, `blocked`, `failed`, or `completed` through the result envelope, while child capability providers return only handoffs. This is capability orchestration, not an assumed Skill-to-Skill RPC API. Neither the parent nor a child provider may replace the director's story, style, route, confirmation, or QA decisions.

For route `dashiai`, read `references/dashiai-adapter.md` and run `scripts/check_dashiai_adapter.py` before planning concrete layouts.

## Run Package

New runs use:

```text
outputs/<deck-slug>/<run-id>/
  director-package/
    run-manifest.json
    user-confirmation.md
    deck-brief.md
    outline.md
    style-match.md
    style-board.md
    media-plan.json
    production-route.md
    motion-plan.json        # required when motion is requested
    qa-report.md
  artifacts/
```

`run-manifest.json` conforms to `contracts/run-manifest.schema.json` and is the machine-readable source of truth. Its append-only `state_history` proves the accepted call order. Validate it with `scripts/validate_runtime_payload.py --kind manifest` before every state promotion and before delivery. Markdown files are human-readable views and must not override it. Legacy packages without a manifest may be read, but revisions create a new protocol `1.1` run directory.

## Result Envelope

Agent callers receive a result conforming to `contracts/result.schema.json`. At minimum it contains:

```text
protocol_version, request_id, operation, status, run_id,
resolved_decisions, unresolved_fields, proposed_decisions,
artifacts, verification, warnings, error, next_action
```

Human responses render the same data in concise natural language. They do not use a second decision model.

Before returning to a parent Agent, run `scripts/validate_runtime_payload.py --kind result`. An invalid result envelope is `failed` at result validation; it must not be forwarded as a completed capability response.

## Validation Before Delivery

Run the checks required by the selected renderer, then run:

```bash
python3 scripts/validate_contract.py
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

Do not report success unless the requested artifacts exist and the relevant checks pass.
