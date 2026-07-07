---
name: guozhi-ppt-director
description: Use when turning articles, links, scripts, course assignments, research notes, business plans, or creator topics into high-quality presentations; when the user asks for PPT Director, guozhi PPT, PPTX, slides, webpage slides, deck, presentation, keynote-style, publish-ready slides, or a combined PPT Master, Guizang PPT Skill, and Frontend Slides workflow. Do not use for one-off text summaries that do not need a reusable deck workflow.
---

# Guozhi PPT Director

Turn raw material into a complete presentation production package: deck strategy, page outline, visual direction, production route, final artifact plan, and QA loop.

## Operating Principles

- Treat this as a director workflow, not a single PPT generator.
- Always close the loop: input -> brief -> story -> style -> route -> production -> QA -> delivery.
- Separate judgment from generation: use this Skill for structure, routing, style direction, and review; use external PPT tools only after the route is chosen.
- Preserve editable outputs when the user needs schoolwork, business delivery, or team collaboration.
- Prefer a visual web version when the user needs motion, screen recording, product-launch style, or short-video reuse.
- Ask only for missing information that changes the result. If the user gives little detail, use the defaults in `templates/deck-brief.md`.

## Default Output Contract

Every run should produce or clearly draft these five artifacts:

1. `deck-brief.md` - goal, audience, occasion, core thesis, tone, constraints.
2. `outline.md` - page-by-page title, message, visual idea, speaker note.
3. `style-board.md` - visual style, layout rules, color, typography, reference direction.
4. `production-route.md` - selected route: PPTX, Frontend Slides, or dual version.
5. `qa-report.md` - logic, visual hierarchy, editability, motion, and delivery checks.

## Workflow

1. Build the deck brief.
   - Identify audience, purpose, usage occasion, final file type, page count, language, deadline, and whether the deck will be spoken, submitted, recorded, or reused as content.
   - If unclear, default to `8-12` pages, Chinese, structured for a 3-5 minute explanation, with both editable and visual reuse in mind.

2. Extract the core thesis.
   - State the one-sentence conclusion the deck must prove.
   - Convert raw material into 3-5 supporting arguments.
   - Remove details that do not support the conclusion.

3. Design the page story.
   - Draft the page-by-page outline using `templates/outline.md`.
   - Each page needs one job only: hook, context, pain, method, workflow, evidence, demo, result, risk, next action, or close.
   - Keep slide text short; put detailed explanation into speaker notes.

4. Choose the visual direction.
   - Read `references/style-routing.md` when the user asks for high aesthetics, Guizang style, design direction, keynote style, magazine style, Swiss grid, technology style, or motion-friendly slides.
   - Create `style-board.md` before generation.
   - Do not let style override clarity.

5. Choose the production route.
   - Read `references/output-routes.md` before committing to a route.
   - Use PPT Master route for editable `.pptx` deliverables.
   - Use Frontend Slides route for HTML, motion, web presentation, screen recording, or video reuse.
   - Use dual route when the user wants both formal submission and viral/visual presentation.

6. Prepare adapter instructions.
   - Read `references/adapter-contract.md` when calling, installing, or delegating to PPT Master, Guizang PPT Skill, Frontend Slides, or another deck generator.
   - Pass only the relevant artifact package: brief, outline, style-board, and route.
   - If the external tool is unavailable, produce the adapter-ready prompt and file structure so the user can run it later.

7. QA before delivery.
   - Read `references/qa-checklist.md`.
   - Check story logic, page density, design consistency, editability, motion feasibility, source attribution, and final file list.
   - Revise once if the QA report finds blocking issues.

## Resource Routing

- Use `templates/deck-brief.md` for missing-input defaults and the brief format.
- Use `templates/outline.md` for page planning.
- Use `templates/style-board.md` for visual direction.
- Use `templates/qa-report.md` for final review.
- Read `references/style-routing.md` for aesthetic decisions.
- Read `references/output-routes.md` for PPTX vs HTML vs dual-version routing.
- Read `references/adapter-contract.md` before using PPT Master, Guizang PPT Skill, Frontend Slides, or equivalent external tools.
- Read `references/qa-checklist.md` before claiming a deck package is ready.

## Validation

Run the structural validator after editing this Skill:

```bash
python3 /Users/guozhi/.codex/skills/standard-skill-maker/scripts/validate_skill.py /Users/guozhi/.codex/skills/guozhi-ppt-director
```

For a realistic prompt check, test one formal PPT request and one motion-web request:

```text
Use guozhi-ppt-director to turn this AI workflow assignment into an 8-page editable PPTX.
```

```text
Use guozhi-ppt-director to turn this product idea into a launch-style animated web deck for screen recording.
```

The Skill passes when the response creates the five required artifacts and chooses the route before generation.
