# Layout Contracting

Use this reference after `style-match.md` and before final PPTX/HTML generation. It borrows the **method** of template-driven deck generation without copying any external template code, runtime, assets, or page designs.

## Why This Exists

Good-looking generated decks are usually not freehand drawings. They use a constrained system:

- one visual theme at a time
- page roles such as cover, statement, context, metrics, comparison, process, action, and closing
- a fixed layout skeleton per page
- explicit text budgets
- known media slots
- validation that prevents default template copy and broken layouts

For `guozhi-ppt-director`, keep the existing Style Library Replica workflow, but add a **layout contract layer** so the renderer fills a chosen visual grammar instead of improvising slide-by-slide.

## External Reference Boundary

Do not copy DashiAI's AGPL-licensed theme runtime, React components, layout manifest, preview assets, CSS, fonts, exported screenshots, or template page designs into this Skill unless the user explicitly accepts the license and integration scope.

Allowed:

- learn the workflow pattern
- describe theme categories in our own words
- create original layout contracts from our own style packs
- use user-provided or public references already added to our style library

Not allowed by default:

- vendoring DashiAI files
- recreating its exact 12 themes or 1020 page components
- copying its sample copy, screenshots, component names, or visual compositions

## Page Role Set

Use these roles when planning a deck. Pick only roles the confirmed page count needs:

| Role | Use For |
| --- | --- |
| `cover` | title, hook, opening tension |
| `statement` | core thesis, key judgment, big idea |
| `breakdown` | agenda, structure, framework overview |
| `context` | background, audience setup, problem framing |
| `metrics` | key numbers, scorecards, chart claims |
| `trend` | timeline, sequence, change over time |
| `comparison` | before/after, options, contrast, matrix |
| `relationship` | system map, cause chain, architecture, ecosystem |
| `case` | example, story, evidence snapshot |
| `process` | steps, workflow, implementation route |
| `risks` | caveats, blockers, assumptions, FAQs |
| `actions` | recommendations, next steps, checklist |
| `closing` | synthesis, decision, final action |

## Layout Contract Shape

For each output slide, define this before rendering:

```text
slide:
  page:
  role:
  reference_role:
  skeleton:
  visible_text_budget:
  media_slots:
  diagram_slots:
  data_slots:
  fixed_style_rules:
  forbidden_changes:
```

Definitions:

- `reference_role`: the closest role in the selected style pack, such as `cover`, `body`, `process`, `compare`, `data`, or `closing`.
- `skeleton`: the arrangement to preserve, for example "large centered title + right visual panel + bottom caption".
- `visible_text_budget`: max visible text by title/body/list/code. Shorten content before shrinking text.
- `media_slots`: images/screenshots/videos needed, or `none`.
- `diagram_slots`: native PPT shapes, connectors, tables, or charts needed.
- `data_slots`: chart/table content and chart insight copy.
- `fixed_style_rules`: palette, type hierarchy, margins, card geometry, line weights, and page rhythm from the selected style pack.
- `forbidden_changes`: source reference text, logos, exact images, exact compositions, and unconfirmed style mixing.

## Production Rules

- Choose one primary style pack first, then create layout contracts from that pack's page-role grammar.
- Do not make every page imitate the cover. Map body pages to body/process/data/compare evidence when available.
- Treat the selected style pack as a design system: palette, typography, spacing, density, shape vocabulary, and page-role cadence.
- Keep each slide to one narrative job. If a page needs two jobs, split or simplify.
- Use short visible text and move detail into speaker notes when the deck has notes.
- When text exceeds the budget, rewrite the message instead of changing the template's typography.
- Use editable PPTX objects for text, shapes, tables, charts, and diagrams where possible.
- Use images only for source visuals or generated visual assets; do not rasterize a whole editable slide just to make it look better.
- No repeated layout skeletons unless the repeated rhythm is intentional and recorded in the layout contract.
- QA must check both style fidelity and contract fit: the output should look like the chosen style pack while respecting text/media budgets.

## Practical Advantage Checklist

Use this checklist when improving a deck:

- Did the user confirm style, page count, output route, and notes?
- Is there exactly one primary style pack lock?
- Does every slide have a role and one narrative job?
- Does every slide have a layout skeleton before rendering?
- Are visible text budgets short enough for the chosen style?
- Are media slots real, staged, and non-duplicated?
- Are charts or diagrams paired with an insight sentence?
- Did validation catch default or unrelated template text?
- Did QA inspect rendered output, not just source code?
