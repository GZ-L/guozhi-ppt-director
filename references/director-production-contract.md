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
- `production-route.md`
- source files and citation notes

## Renderer Instructions

For editable PPTX:

- Use editable text, shapes, tables, charts, and image placeholders where possible.
- Avoid image-only slides unless the source itself is an image and editability is impossible.
- Keep speaker notes and source notes when relevant.
- Render or open the file for visual QA when tooling is available.
- If Style Library Replica is selected, build against the primary style pack lock when available. Match the reference's palette, typography mood, spacing, layout rhythm, shape treatment, and density before adding any decorative ideas. Do not invent a hybrid style.
- If a primary style pack is selected, map each output slide to the closest pack role before building. Do not make every body page imitate the pack's cover page.
- Before creating slide objects, write a lightweight layout contract for every slide. Preserve the chosen skeleton and text/media budgets during rendering; shorten copy before shrinking type or adding extra boxes.
- Do not copy external template engines, AGPL-licensed theme files, or third-party template assets into this Skill unless the user explicitly approves that integration. Use external systems as method references only.

For visual web deck:

- Build previewable slides with stable dimensions.
- Verify that text is not overlapping or off-frame.
- Keep motion purposeful: reveal structure, sequence, or contrast.
- Export images, PDF, or video only when requested.
- If Style Library Replica is selected, compare screenshots against the primary reference during QA and revise any obvious drift.

For dual version:

- Keep one shared outline and terminology.
- QA each version separately.
- Do not let the visual version drift away from the editable version's facts.

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
