# Guozhi PPT Director Maintenance Spec

This is the authority for modifying `guozhi-ppt-director`. Read it before changing the Skill's behavior, identifiers, call order, references, templates, adapters, scripts, or style library.

## Maintenance Boundary

- Runtime behavior is defined by `CALLING_SPEC.md` and machine contracts under `contracts/`.
- This file defines how maintainers keep those runtime materials synchronized.
- Do not edit the installed Skill during a deck production run.
- Preserve unrelated user changes and existing style assets unless the maintenance request explicitly changes them.
- Use a failing regression test before changing behavior.

## Source Of Truth

| Concern | Authority | Dependent Files |
| --- | --- | --- |
| Skill trigger and top-level routing | `SKILL.md` | `agents/openai.yaml`, `OVERVIEW.md` |
| Runtime operations, state, order, precedence | `CALLING_SPEC.md` | request/result schemas, templates, interaction references |
| Route IDs and route capabilities | `contracts/route-registry.json` | output routes, adapters, templates, QA |
| Invocation fields | `contracts/invocation.schema.json` | calling spec, run manifest, Agent examples |
| Result states and fields | `contracts/result.schema.json` | calling spec, run manifest, QA report |
| Run-specific machine state | `templates/run-manifest.json` | Markdown run-package views |
| Style inventory | style-pack and legacy indexes | catalog, contact sheets, style-routing rules |
| Renderer behavior | adapter reference for that renderer | route registry, production contract, QA checks |

When two files disagree, fix the dependent file. Do not create a second authority.

## Stable Identifiers

- Skill name: `guozhi-ppt-director`.
- Protocol version format: `MAJOR.MINOR`.
- Operation IDs use `domain.verb`, except `help`.
- Route IDs use lowercase snake case.
- Run states use lowercase snake case.
- Style IDs remain stable after publication; update metadata in place instead of reusing an ID for another visual source.
- User-facing translations never replace internal identifiers.

Unqualified letter choices are presentation labels, not protocol identifiers, and are not permitted in runtime contracts.

## Change Impact Matrix

| Change | Files That Must Be Reviewed And Usually Updated |
| --- | --- |
| Add, remove, or rename an operation | calling spec, invocation schema, result schema, run manifest, tests, overview |
| Add, remove, or rename a route | route registry, calling spec, output routes, relevant adapter, templates, QA, tests |
| Change a run state or transition | calling spec, result schema, run manifest, confirmation and QA templates, tests |
| Change confirmation behavior | calling spec, question layer, user-confirmation template, tests |
| Change style scoring or eligibility | style-match rules, style routing, catalog rules, style-match template, tests |
| Add or change a renderer | route registry, adapter reference, production contract, capability check, QA |
| Add or change source extraction | calling spec source normalization, adapter instructions, evidence fields, tests |
| Add or update a style pack | pack directory, pack metadata, pack index, catalog, contact sheet, asset validation |
| Change output paths | calling spec, run manifest, production route, QA report, tests |
| Change a script dependency | script discovery logic, maintenance dependency notes, capability check, tests |

## Compatibility Rules

- Backward-compatible additions increment the minor version.
- Removing or changing the meaning of an operation, route, state, or required field increments the major version.
- Never reuse an old identifier with a new meaning.
- Legacy run packages are read-only inputs. Revisions write a new current-version manifest.
- External renderer checks must report version and capability when available; file presence alone is not enough to claim a render will succeed.
- User-specific absolute paths are forbidden in runtime scripts and contracts.
- Network collection verifies TLS by default.

## Agent Compatibility

The Skill must support both interaction modes through the same protocol:

- `human` may render a concise recommendation and questions.
- `agent` returns a structured result and never talks directly to the end user.

Any new capability must define:

1. operation or capability role;
2. required inputs;
3. produced outputs;
4. allowed state transitions;
5. mutation scope;
6. failure and retry behavior;
7. validation command.

Do not require another Skill by path. Refer to a capability role or discover an installed Skill at runtime.

## Editing Procedure

1. Read `SKILL.md`, `CALLING_SPEC.md`, this file, and the authority file for the requested change.
2. Identify the smallest affected file set using the change impact matrix.
3. Add or update a regression test that fails for the current behavior.
4. Run the test and verify the expected failure.
5. Make the smallest implementation change.
6. Run the focused test until it passes.
7. Run contract, structure, asset, and script validation relevant to the change.
8. Inspect `git diff` and confirm no unrelated asset or metadata churn.
9. Report files changed, commands run, results, and any unverified capability.

## Required Validation

For every behavioral or protocol change:

```bash
python3 scripts/validate_contract.py
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 "$HOME/.codex/skills/standard-skill-maker/scripts/validate_skill.py" .
python3 "$HOME/.codex/skills/.system/skill-creator/scripts/quick_validate.py" .
```

For style-library changes, also verify that every indexed pack directory and referenced asset exists. For renderer changes, run its capability check and one minimal render/export test when the environment permits.

## Release Gate

The Skill is ready only when:

- all authority and dependent files use the same identifiers;
- no runtime document redefines a route, operation, or state;
- tests cover the changed behavior and pass;
- contract and Skill validators pass;
- required external capabilities are either verified or reported as unavailable;
- no generated caches, temporary downloads, secrets, or unrelated files are included.
