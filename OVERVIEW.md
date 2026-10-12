# Guozhi PPT Director Overview

`guozhi-ppt-director` turns source material into a confirmed presentation package and checked PPTX, web deck, PDF, or review. It also manages the built-in style library. `CALLING_SPEC.md` is the runtime authority; `MAINTENANCE_SPEC.md` is the modification authority.

Protocol `1.1` adds capability-gated motion, video, visual-intent planning, and confirmation-scoped media handoffs. Static `1.0` calls remain accepted and normalize to motion profile `none`.

## Capability Map

| Operation | Result |
| --- | --- |
| `deck.create` | new presentation package and confirmed artifacts |
| `deck.revise` | scoped revision in a new protocol run |
| `deck.review` | evidence-based issue list without rendering |
| `style.list` | style inventory or filtered inspection |
| `style.add` | new approved style reference or pack |
| `style.update` | refreshed style metadata, roles, or assets |
| `style.remove` | explicitly confirmed style removal |
| `help` | usage and capability explanation |

Motion profiles are `web_motion_v1`, `pptx_basic_v1`, and `dual_motion_v1`. General animation requests produce a run-specific `motion-plan.json` with grouped in-slide choreography, visible card/image entrance variety, and stable names resolved to final exported PPTX Shape IDs; page transitions or unexplained all-fade output are accepted only when explicitly constrained. Requested visuals use a validated `media-plan.json`: content-bearing source media and native PPT structure precede generated assets, and real images from the selected style pack lock dimensionality, material, lighting, depth, photography/CGI/illustration method, crop, and scale. When a subject is missing, external analysis is `visual_intent_only`; it chooses what to depict while the selected template still controls how the image looks. Optional IP capability never contributes its original skin or changes the deck style. A run records `verification_required` and can complete only with matching structural or playback evidence. Every produced deck also requires one full-size slide preview per page; montage is navigation only. Object-level layout output must pass declared surface collision verification.

## Runtime Sequence

```text
request -> normalize -> provisional brief/visual needs -> capability/three-style recommendation
-> needs_input or confirmed -> final plan/layout/media contracts -> render -> QA -> result
```

Human and Agent callers use the same state machine. Human mode renders concise natural language. Agent mode returns the result schema and leaves end-user interaction to the parent Agent.

The package works as a standalone Skill or as one function under a parent Agent. Skills are declarative, so the host Agent executes provider discovery, tools, and child-Skill calls. In standalone Skill mode, the director instructs its host Agent to discover source, media, renderer, and QA providers by capability role and validates every capability handoff. In parent Agent mode, the parent calls the director once with `interaction_mode: agent`; child Skills never become a second director and never contact the end user. No separate Skill-to-Skill RPC mechanism is assumed.

Natural-language calls use `contracts/intent-registry.json`; structured Agent calls run through `scripts/validate_runtime_payload.py` before manifest mutation. Unresolved library styles use a deterministic three-candidate set conforming to `contracts/style-selection.schema.json`, with one recommendation and two visually distinct previews. The manifest follows `contracts/run-manifest.schema.json` and records append-only state history. Capability providers exchange `contracts/capability-handoff.schema.json` records, and result envelopes are validated before return.

## Architecture

| Layer | Authority |
| --- | --- |
| Trigger and top-level workflow | `SKILL.md` |
| Runtime protocol and collaboration | `CALLING_SPEC.md` |
| Modification protocol | `MAINTENANCE_SPEC.md` |
| Machine identifiers and envelopes | `contracts/` |
| Interaction rendering | `references/question-layer.md` |
| Story, style, layout, route, and QA guidance | `references/` |
| Run state and human-readable views | `templates/` |
| Deterministic checks and collection | `scripts/`, `tests/` |
| Motion and video policy | `references/motion-video-delivery.md` |
| Visual intent and media style sovereignty | `contracts/media-plan.schema.json`, `references/visual-intent-analysis.md` |
| Visual references | `assets/style-library/` |

## Output Layout

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
    qa-report.md
  artifacts/
```

The JSON manifest is the source of truth. Markdown files are human-readable views.

## Maintenance

Use the change-impact matrix and user-reported defect loop in `MAINTENANCE_SPEC.md`. Reproducible systemic defects require a minimal reproducer, failing regression test, authority/dependent-file updates, and full validation. Protocol changes must update their machine contracts and tests. Style-library changes must keep pack metadata, indexes, catalog entries, contact sheets, and assets aligned.
