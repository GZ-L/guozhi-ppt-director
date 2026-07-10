---
name: guozhi-ppt-director
description: Use when a user or Agent needs to create, revise, review, or beautify a presentation from articles, PDFs, links, scripts, research, business material, or creator topics; manage the presentation style library; or coordinate PPTX, web-deck, PDF, and DashiAI presentation output. Do not use for one-off summaries that do not need a presentation workflow.
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
- Never copy reference text, logos, brands, people, characters, exact artwork, claims, or exact page composition.

## Workflow

1. Classify one stable operation from `CALLING_SPEC.md`.
2. Create or load `templates/run-manifest.json` and normalize sources and constraints.
3. Check required fields, renderer capabilities, and style eligibility.
4. Recommend one complete configuration or return structured `needs_input`.
5. Freeze confirmed decisions, then build the brief, outline, style lock, layout contracts, and production route.
6. Render through the confirmed adapter only after state `confirmed` and `planned`.
7. QA requested artifacts and return `completed`, `blocked`, or `failed` with evidence.

## Resource Routing

- `CALLING_SPEC.md`: runtime operations, identifiers, precedence, state machine, call order, coordination, and result contract.
- `MAINTENANCE_SPEC.md`: change ownership, synchronization, compatibility, and release validation.
- `contracts/`: machine-readable route, invocation, and result contracts.
- `OVERVIEW.md`: concise capability and architecture map.
- `README.md`: installation, public usage, examples, validation, and publication boundaries.
- `NOTICE.md`: ownership, third-party reference, and external-renderer boundaries.
- `examples/REAL_CASES.md`: real interaction and regression cases for users and Agent integrators.
- `references/question-layer.md`: human and Agent confirmation rendering.
- `references/style-routing.md`: style selection and fidelity gate.
- `references/style-library/README.md`: style-library add, update, and collection procedures.
- `references/style-library/style-match-rules.md`: deterministic eligibility, scoring, and tie-break rules.
- `references/style-library/zcool-style-catalog.md`: built-in reference catalog.
- `references/layout-contracting.md`: page roles, skeletons, text budgets, and media slots.
- `references/output-routes.md`: stable route definitions.
- `references/dashiai-adapter.md`: external DashiAI renderer contract for route `dashiai`.
- `references/director-production-contract.md`: renderer boundary and output requirements.
- `references/qa-checklist.md`: story, visual, route, state, and delivery checks.
- `templates/`: run-manifest source plus human-readable run-package views.
- `scripts/check_dashiai_adapter.py`: external DashiAI capability check.
- `scripts/validate_contract.py`: protocol, reference, style-asset, and portability validation.

Published source checkouts contain style metadata but intentionally exclude third-party bitmap references. A missing local style asset makes that style ineligible at runtime; it never authorizes an unreferenced visual guess. Use `python3 scripts/validate_contract.py --require-style-assets` when validating a local installation that is expected to contain the complete authorized asset set.

## Validation

After changing the Skill, run:

```bash
python3 scripts/validate_contract.py
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 "$HOME/.codex/skills/standard-skill-maker/scripts/validate_skill.py" .
python3 "$HOME/.codex/skills/.system/skill-creator/scripts/quick_validate.py" .
```
