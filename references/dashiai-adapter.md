# DashiAI Adapter

Use this reference only when the confirmed route ID is `dashiai` or the caller explicitly requests DashiAI capability information.

## Boundary

`guozhi-ppt-director` remains the director. DashiAI is an external renderer and template asset dependency after the run manifest contains confirmed audience, page count, speaking time, rewrite boundary, deliverable, theme, media intent, story, and layout contracts.

DashiAI uses AGPL-3.0. Keep it external. Do not vendor its runtime, components, CSS, fonts, layout manifest, previews, or theme assets into this Skill.

## Capability Check

Run:

```bash
python3 scripts/check_dashiai_adapter.py
```

Record:

- installed and usable state;
- Skill and project paths;
- runtime version when available;
- theme-grid path;
- Node dependency state;
- missing capabilities.

File presence is not a completed render check. If required runtime capability is missing, return `blocked` with the exact next action.

## Theme Recommendation

Recommend one theme after route `dashiai` is confirmed. Show the theme grid in human mode when available; return its path in Agent mode.

| Theme | Best Fit |
| --- | --- |
| `theme01` | light product intro and company report |
| `theme02` | AI, technology launch, robotics, innovation |
| `theme03` | developer talk, architecture, technical plan |
| `theme04` | young consumer brand and creator pitch |
| `theme05` | data report, KPI, market analysis |
| `theme06` | dense strategy, industry, investment analysis |
| `theme07` | research, white paper, policy, academic work |
| `theme08` | premium launch and high-end technology proposal |
| `theme09` | deep-blue brand story and editorial profile |
| `theme10` | finance and index-heavy work only |
| `theme11` | growth review, fundraising, business plan |
| `theme12` | music, entertainment, trend event |

Use explicit content and density evidence. If the user rejects the recommendation, show at most two qualified alternatives.

## Required Decisions

Before rendering, the manifest must contain:

- `route_id: dashiai`;
- exact DashiAI theme;
- media intent: none, provided, generated, or reserved slots;
- final deliverables;
- install/capability check result;
- confirmed page-level story and layout contracts.

## Production Steps

1. Complete the director package and set state `planned`.
2. Convert the confirmed outline and contracts into DashiAI `goal.json`.
3. Use concrete `layout + props` for every slide.
4. Run `layout:query` and `inspect:layout` before filling complex props.
5. Respect fill plans, visible item counts, media slots, and text budgets.
6. Run `props:safe -- --goal <goal.json> --write`.
7. Run `validate:goal-spec`.
8. Render into the current run directory.
9. Run `validate:swiss` and `validate:goal-copy`.
10. Export requested artifacts and inspect rendered pages.
11. Record commands, results, paths, and limitations in the manifest and QA report.

## Run Directory

```text
outputs/<deck-slug>/<run-id>/
  director-package/
  dashiai/
    goal.json
    goal.fill-plan.json
    ppt/
      index.html
      assets/
    exports/
  artifacts/
```

## Failure Behavior

- Missing installation or runtime capability: `blocked`.
- Invalid goal or output validation: `failed` at the recorded stage.
- Export unavailable after valid HTML render: return the verified HTML artifact, keep the requested export unresolved, and do not report `completed` for the full request.
- Renderer changes require explicit approval; never fall back silently.
