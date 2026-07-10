# QA Checklist

Use before saying a presentation package is ready.

## Logic

- The deck has one clear thesis.
- Every page supports the thesis.
- The page order creates a visible argument.
- The opening explains why the audience should care.
- The close gives a next action, takeaway, or decision.

## Slide Density

- One main message per page.
- No page is used as a document dump.
- Speaker notes hold details that do not belong on the slide.
- Titles say the point, not just the topic.

## Visual Quality

- Style is consistent across cover, section pages, body pages, and closing page.
- Alignment, spacing, and hierarchy are intentional.
- Colors are not one-note unless the brief requires strict branding.
- Screenshots, charts, and diagrams are readable.

## Route Fit

- `run-manifest.json` is the machine source of truth and records protocol version, request ID, run ID, operation, route, and state.
- Rendering started only after states `confirmed` and `planned`.
- PPTX route: text and shapes should be editable where possible.
- Visual web route: motion helps comprehension, not decoration only.
- Dual route: both versions share the same story and style.
- Route `dashiai`: route, theme, media intent, and install state were explicitly confirmed before production.
- Route `dashiai`: DashiAI was used only as renderer/template engine after the Guozhi director package was complete.
- The user confirmation gate was satisfied before final production.
- No second PPT Skill was used as a separate director.

## Style Library Fit

- The selected references match topic, audience, density, and route.
- The style mode is explicit: Style Library Replica.
- If a style pack is available, output slide roles map to pack roles instead of repeatedly copying the cover.
- If the selected reference is cover-only, the limitation is recorded and accepted before production.
- The deck visibly matches the primary reference's palette, typography mood, spacing, composition rhythm, shape vocabulary, image treatment, and density.
- The deck replicates style instead of copying source content, logos, characters, products, people, exact artwork, or page-specific compositions.
- The fidelity lock is recorded: primary reference, match closely, do not copy, extension method, and allowed director freedom.
- The final style system works for cover, body, diagrams, and closing pages.

## DashiAI Adapter Fit

- Route `dashiai` was selected explicitly.
- `scripts/check_dashiai_adapter.py` was run and recorded.
- The chosen DashiAI theme matches topic, audience, density, and media needs.
- Final DashiAI slides use concrete `layout + props`, not draft-only `role`.
- DashiAI `goal.json` is under the deck output folder, not inside the DashiAI Skill.
- DashiAI validations ran: goal spec, rendered deck, default-copy check, and export check when requested.
- DashiAI output has no unrelated default template copy.
- Missing DashiAI install or export failures were reported instead of silently switching route.

## Delivery

- Final state is `completed` only when every requested artifact exists and is checked.
- Final file names are clear.
- Source notes or links are preserved.
- Known limitations are listed.
- Next revision suggestions are concrete.
