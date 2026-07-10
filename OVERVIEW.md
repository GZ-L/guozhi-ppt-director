# Guozhi PPT Director Overview

`guozhi-ppt-director` turns source material into a confirmed presentation package and checked PPTX, web deck, PDF, or review. It also manages the built-in style library. `CALLING_SPEC.md` is the runtime authority; `MAINTENANCE_SPEC.md` is the modification authority.

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

## Runtime Sequence

```text
request -> normalize -> provisional brief -> capability/style recommendation
-> needs_input or confirmed -> final plan/layout contracts -> render -> QA -> result
```

Human and Agent callers use the same state machine. Human mode renders concise natural language. Agent mode returns the result schema and leaves end-user interaction to the parent Agent.

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
    production-route.md
    qa-report.md
  artifacts/
```

The JSON manifest is the source of truth. Markdown files are human-readable views.

## Maintenance

Use the change-impact matrix in `MAINTENANCE_SPEC.md`. Protocol changes must update their machine contracts and tests. Style-library changes must keep pack metadata, indexes, catalog entries, contact sheets, and assets aligned.
