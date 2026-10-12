# Style Match Rules

Use these rules to produce a deterministic `style_candidates` set from explicit run inputs. It contains three eligible style candidates: one recommended candidate and two visual alternatives. Selection is never random.

## Eligibility

- `status: ok` packs are eligible.
- `status: limited` packs are eligible only when the invocation explicitly sets `allow_limited_style: true` or the user confirms the coverage limitation.
- Legacy single images are `cover-only` and are ineligible for multi-page production unless that limitation is explicitly accepted.
- Exclude references that conflict with required brand, density, media, readability, or route constraints.

## Scoring

Score each eligible candidate from 0 to 2 on eight dimensions:

| Dimension | 0 | 1 | 2 |
| --- | --- | --- | --- |
| Topic | conflicts | broadly usable | directly matches |
| Audience | unsuitable | neutral | directly suitable |
| Occasion | unsuitable | adaptable | directly suitable |
| Mood | conflicts | partial | matches explicit mood |
| Density | cannot hold content | requires simplification | matches content density |
| Deliverable | incompatible | usable with risk | native fit |
| Media | no usable treatment evidence | partial image treatment evidence | direct multi-role evidence for dimensionality, material, lighting, depth, and image method |
| Role coverage | missing critical roles | gaps accepted | covers all required roles |

Minimum recommendation score: `10/16` with no zero in deliverable or role coverage.

Record each score and one evidence phrase. Do not replace the total because another reference “feels better.”

## Repeat Penalty

- Read `recent_style_ids` from up to the three most recent completed deck manifests available to the caller. Use an empty list when no history is available.
- Subtract `2` from a candidate's fit score when its ID appears in `recent_style_ids`; otherwise subtract `0`.
- `effective_score = fit_score - repeat_penalty`.
- An explicitly rejected style ID is ineligible for the current run.
- The penalty changes deterministic ranking; it is not random rotation.

## Candidate Construction

1. Sort eligible candidates by effective score, then apply the tie-break rules below.
2. Rank the highest candidate as `recommended_style_id`.
3. Select the highest remaining candidate with a different indexed `visual_family` as visual alternative 1.
4. Select the highest remaining candidate whose indexed `visual_family` differs from both prior candidates as visual alternative 2.
5. Require readable Preview asset files for all three candidates.
6. Serialize with `contracts/style-selection.schema.json` and validate using `scripts/validate_runtime_payload.py --kind style_selection`.

If three qualified visual families are unavailable, return `needs_input`; do not lower the fit threshold, reuse a visual family, or fill the set randomly.

## Tie-Break

Resolve equal totals in this order:

1. higher role-coverage score;
2. higher density score;
3. higher deliverable score;
4. more required roles with direct assets;
5. lexicographically smaller stable style ID.

## Style Lock

After confirmation:

1. Lock one primary style ID.
2. Decompose palette, contrast, typography, scale, grid, margins, spacing, density, image treatment, geometry, line weight, radius, shadows, and cover/body cadence.
3. Map every output slide to a direct reference role or a documented gap.
4. Create the layout contract before rendering.
5. Use a secondary reference only after explicit approval and only for a documented missing role.

## Fidelity Boundary

Match the selected visual language closely while preserving readability, editability, source accuracy, and safety. Do not copy source text, logos, brands, named products, people, characters, exact subjects, exact artwork, page-specific charts, claims, or exact compositions.

## Required Output

Write the result into the run manifest and `style-match.md`:

- input evidence;
- candidate scores;
- `style_candidates` and `recommended_style_id`;
- recent-style evidence, repeat penalties, indexed visual families, and Preview asset paths;
- recommended and confirmed style IDs;
- selected assets and role coverage;
- fidelity rules and prohibited content;
- page-role mapping and layout contracts;
- risks and accepted limitations;
- visual QA checks.
