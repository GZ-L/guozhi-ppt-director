# Adapter Contract

Use this file before calling or handing off to PPT Master, Guizang PPT Skill, Frontend Slides, or another deck tool.

## Director Responsibilities

The director must provide:

- Deck brief.
- Page outline.
- Style board.
- Production route.
- QA requirements.
- Source material and citation notes when available.

The director must not assume:

- The external tool is installed.
- The external tool can access private files.
- A generated PPT is editable unless the route explicitly guarantees editable objects.
- A generated HTML deck is suitable for submission unless the user accepts that format.

## PPT Master Adapter

Use for:

- Editable `.pptx`.
- Business/school/report decks.
- Structured, page-by-page generation.

Prompt package:

```text
Goal: [from deck-brief]
Audience: [from deck-brief]
Page count: [from deck-brief]
Style: [from style-board]
Pages: [from outline]
Need editable objects: yes
Deliverable: pptx
QA: avoid image-only slides unless unavoidable
```

## Guizang PPT Skill Adapter

Use for:

- Style exploration.
- High-aesthetic layout directions.
- Cover concepts.
- Visual language and page rhythm.

Prompt package:

```text
Use this material to design the visual direction, page rhythm, and high-aesthetic layout rules.
Do not generate final slides yet.
Return: style keywords, cover direction, layout rules, typography, color, page examples.
```

## Frontend Slides Adapter

Use for:

- HTML slides.
- Motion and transitions.
- Launch-style visual presentation.
- Screen recording or video reuse.

Prompt package:

```text
Goal: [from deck-brief]
Audience: [from deck-brief]
Style: [from style-board]
Pages: [from outline]
Motion: include transitions, reveal order, and viewport-safe layouts
Deliverable: HTML slide project
QA: verify desktop and mobile preview if applicable
```

## Fallback

If the selected external tool is unavailable, return:

- The selected route.
- The adapter prompt.
- The expected folder/file structure.
- Manual next steps for running the external tool later.
