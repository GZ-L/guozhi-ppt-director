# Style Routing

Use this file after source normalization and provisional page-role planning. Style identifiers come from the style indexes or the confirmed DashiAI theme list.

## Inputs

Record explicit or proposed values for:

- topic and source type;
- audience and occasion;
- route and deliverable;
- user mood words;
- density;
- required page roles;
- media and brand constraints;
- whether limited coverage is allowed.

## Native And Web Style Workflow

1. Read `references/style-library/style-match-rules.md`.
2. Load the catalog and style indexes.
3. Inspect candidate pack contact sheets and page-role assets.
4. Exclude ineligible references.
5. Score every remaining candidate with recorded evidence.
6. Apply the deterministic repeat penalty and visual-family diversity rules from the match rules.
7. Build and validate exactly three candidates: one recommended candidate and two visual alternatives with different indexed visual families and readable previews.
8. In human mode, show all three previews together and identify `recommended_style_id`.
9. In Agent mode, return the validated `style_candidates` object under `proposed_decisions` until confirmed.
10. Lock the confirmed reference in the run manifest and `style-match.md`.
11. Convert its page-role grammar into layout contracts.

## DashiAI Style Workflow

Use only for confirmed route `dashiai`:

1. Read `references/dashiai-adapter.md`.
2. Run the adapter capability check.
3. Score eligible themes against topic, audience, density, and media needs.
4. Recommend one theme and record the grid path when available.
5. Lock the confirmed theme before concrete layout selection.

## Fidelity Gate

Reject or return `needs_input` when:

- no eligible reference reaches the minimum score;
- a reference lacks required page roles and limited coverage was not accepted;
- the proposed treatment makes confirmed content unreadable;
- required media cannot fit the reference grammar;
- the output would copy protected source content instead of visual language;
- more than one primary reference is selected.

## Style Contract

The final style contract records:

- primary style ID and exact asset paths;
- eligibility and score evidence;
- fidelity target and traits to match;
- prohibited source content;
- output-role to reference-role mapping;
- layout skeletons and visible text budgets;
- color, typography, spacing, geometry, and media treatment;
- documented role gaps and accepted limitations;
- visual QA comparisons.
