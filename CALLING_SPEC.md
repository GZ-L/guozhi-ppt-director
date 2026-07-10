# Guozhi PPT Director Calling Spec

Protocol version: `1.0`

This is the runtime authority for every `guozhi-ppt-director` invocation. Read it before lower-level references, templates, style catalogs, or renderer instructions. `MAINTENANCE_SPEC.md` governs changes to the Skill; it does not govern a deck run.

## Authority And Failure Rule

1. Follow system, developer, and explicit user instructions.
2. Follow this protocol for classification, state, order, and coordination.
3. Use `contracts/route-registry.json` for route identifiers and the request/result schemas for machine fields.
4. Treat lower-level files as implementation guidance. They cannot redefine an operation, route, state, or transition.
5. When input is ambiguous, return `needs_input`. Never guess and continue to rendering.
6. Never modify this installed Skill during a deck production run. Contract drift is a maintenance task.

## Stable Operations

Use exactly one operation per invocation:

| Operation | Purpose | Mutates Presentation Files | Mutates Style Library |
| --- | --- | --- | --- |
| `deck.create` | Create a new deck from source material | yes | no |
| `deck.revise` | Revise an existing deck or run package | yes | no |
| `deck.review` | Review a deck, outline, style, or workflow | no | no |
| `style.list` | List or inspect available references | no | no |
| `style.add` | Add a new style reference or pack | no | yes |
| `style.update` | Refresh metadata, roles, or assets for an existing style | no | yes |
| `style.remove` | Remove a named style reference or pack | no | yes |
| `help` | Explain capabilities and usage | no | no |

Natural-language classification maps to these identifiers, but the identifier is the source of truth after classification. If two operations are plausible, return `needs_input` with one clarifying question.

## Stable Routes

Use only route identifiers from `contracts/route-registry.json`:

- `native_pptx`
- `web_deck`
- `dual`
- `dashiai`
- `review_only`

User-facing labels may be translated, but never use an unqualified letter as a route identifier. A phrase such as “确认推荐方案” confirms only the single fully specified recommendation in the immediately preceding response.

## Interaction Modes

Every invocation has an `interaction_mode`:

- `human`: communicate with the end user. Recommend one complete configuration and ask only unresolved material questions.
- `agent`: return the structured result envelope to the caller. Do not ask the end user directly and do not present a conversational menu.

An Agent caller may provide already confirmed decisions. When all required fields are present and `confirmation.status` is `confirmed`, continue without another confirmation turn.

## Input Precedence

Resolve every field in this order:

1. Structured fields in the current invocation.
2. Exact decisions in the latest explicit user confirmation.
3. Confirmed values in the referenced `run-manifest.json`.
4. Deterministic defaults, only when `allow_defaults` is `true` or the user explicitly asked to proceed with defaults.
5. Proposed inference, recorded as unconfirmed and never treated as a decision.

Conflicting values at the same or higher level produce `needs_input`. Never silently merge page count, route, style, or deliverable conflicts.

## Required Inputs

| Operation | Required Before Work | Required Before Mutation Or Rendering |
| --- | --- | --- |
| `deck.create` | at least one source item | exact page count, deliverable, route, style lock, rewrite boundary, notes decision, confirmation |
| `deck.revise` | existing deck path or `run_id`; requested revision scope | confirmed revision scope and any changed route/style decisions |
| `deck.review` | deck, package, outline, or source to review | none |
| `style.list` | optional filter | none |
| `style.add` | source reference | generated or confirmed stable style ID and mutation approval |
| `style.update` | existing style ID and replacement/refresh source | mutation approval |
| `style.remove` | existing style ID | explicit destructive confirmation |
| `help` | none | none |

If speaking time is supplied without page count, propose an exact page count before confirmation. A range is not executable and cannot become a confirmed page count.

## Source Normalization

For deck operations, normalize each input into a source record before story planning:

```text
source_id, type, path_or_url, availability, extraction_method,
title, author, date, facts, citations, media, limitations
```

Use available PDF, browser, document, image, or repository capabilities only as source adapters. Record extraction failures and preserve source attribution. Source adapters do not decide story, style, route, or page count.

## State Machine

Allowed run states:

```text
received -> normalized -> needs_input -> confirmed -> planned
planned -> rendering -> qa -> completed
received|normalized|needs_input|confirmed|planned|rendering|qa -> blocked
received|normalized|confirmed|planned|rendering|qa -> failed
```

Rules:

- `needs_input` is resumable and must include unresolved fields plus one recommended resolution.
- `confirmed` requires an exact route ID, exact page count, deliverable, style decision, rewrite boundary, and notes decision for deck production.
- Rendering is forbidden before `confirmed` and `planned`.
- `blocked` means a required external capability or approval is unavailable; include a concrete next action.
- `failed` means execution was attempted and did not complete; include the failed stage and evidence.
- `completed` requires requested artifacts to exist and QA evidence to be recorded.

## Deck Call Order

For `deck.create` and `deck.revise`, follow this order exactly:

1. Create or load `run-manifest.json`; assign `request_id`, `run_id`, operation, and `interaction_mode`.
2. Normalize source material and explicit constraints.
3. Validate required fields and detect conflicts.
4. Build a provisional brief and estimate the page roles needed.
5. Check renderer availability for the requested deliverable.
6. Score eligible style references and produce one recommendation with its exact style ID, fit evidence, and risk.
7. If a material decision is unresolved, set `needs_input` and stop.
8. Freeze confirmed decisions in the manifest.
9. Build the final brief, outline, style lock, layout contracts, and production route.
10. Render through the selected adapter into a temporary or run-specific output directory.
11. Run story, style, route, editability, source, and rendered-output QA.
12. Promote checked artifacts, set `completed`, and return the result envelope.

## Review Call Order

For `deck.review`:

1. Normalize the supplied deck, package, outline, or source.
2. Confirm the requested review scope only when it is ambiguous.
3. Inspect story, source fidelity, style consistency, layout, density, route fit, editability, and rendered output when available.
4. Return findings ordered by severity with file/page evidence and unverified areas.
5. Do not create or revise presentation artifacts inside the review operation.

## Style-Library Call Order

- `style.list`: load indexes, apply any explicit filter, verify referenced assets, and return stable IDs plus coverage and status.
- `style.add`: verify mutation approval, normalize the source, generate a stable unused ID, collect representative roles, write pack metadata and assets, update indexes/catalog/contact sheet, then validate.
- `style.update`: verify mutation approval and existing ID, preserve ID meaning, update only requested metadata or assets, synchronize dependent files, then validate.
- `style.remove`: require explicit destructive confirmation naming the exact ID, remove only that entry and its owned assets, synchronize indexes/catalog/contact sheet, then validate.

If the installed Skill directory is not writable, mutation operations return `blocked`; they do not redirect output silently.

## Help Call Order

For `help`, answer from `SKILL.md`, this protocol, and `OVERVIEW.md`. Explain stable operation and route identifiers. Do not create run artifacts.

## Confirmation Behavior

In `human` mode:

- Lead with one recommended complete configuration.
- State known parameters and ask only for unresolved material decisions.
- Use exact identifiers for route and style.
- Offer alternatives only after the user rejects the recommendation or asks to compare options.
- If the user supplied all decisions and explicitly said to proceed, record confirmation and continue.

In `agent` mode:

- Return `status: needs_input`, `unresolved_fields`, `proposed_decisions`, and `next_action`.
- The parent Agent decides whether to obtain user input or apply authorized defaults.
- Resume with the same `request_id` and `run_id`; do not create a second run for the same confirmation cycle.

## Style Decision

Visual production requires one of these explicit decisions:

- a confirmed style-pack ID from the library;
- `preserve_existing` for a revision that keeps the existing visual system;
- a confirmed DashiAI theme when route `dashiai` is selected.

Score eligible references using `references/style-library/style-match-rules.md`. The highest deterministic score is the recommendation. A `limited` reference is eligible only when the caller explicitly allows limited coverage. If no eligible reference reaches the minimum fit threshold, return `needs_input` and request a new reference.

## Skill And Agent Coordination

`guozhi-ppt-director` is the only director. It owns request classification, story, page jobs, route, style lock, layout contracts, and QA.

Other Skills, tools, or Agents may fill one declared capability role:

- `source_adapter`: extract text, facts, citations, screenshots, or media;
- `media_generator`: create confirmed visual assets for declared media slots;
- `renderer`: convert the confirmed director package into PPTX, HTML, PDF, or images;
- `visual_qa`: inspect rendered pages for overlap, clipping, blank output, or style drift.

Coordination rules:

1. Pass only the fields needed for that capability role.
2. Do not delegate confirmation, style choice, page count, or story ownership.
3. Record the capability name, input, output, version when available, and failure evidence in the run manifest.
4. Validate returned artifacts before using them downstream.
5. Never silently switch renderer or route. Set `blocked` or return `needs_input` for approval.

For route `dashiai`, read `references/dashiai-adapter.md` and run `scripts/check_dashiai_adapter.py` before planning concrete layouts.

## Run Package

New runs use:

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

`run-manifest.json` is the machine-readable source of truth. Markdown files are human-readable views and must not override it. Legacy packages without a manifest may be read, but revisions create a new protocol `1.0` run directory.

## Result Envelope

Agent callers receive a result conforming to `contracts/result.schema.json`. At minimum it contains:

```text
protocol_version, request_id, operation, status, run_id,
resolved_decisions, unresolved_fields, proposed_decisions,
artifacts, warnings, error, next_action
```

Human responses render the same data in concise natural language. They do not use a second decision model.

## Validation Before Delivery

Run the checks required by the selected renderer, then run:

```bash
python3 scripts/validate_contract.py
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

Do not report success unless the requested artifacts exist and the relevant checks pass.
