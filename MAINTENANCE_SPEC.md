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
| Intent classification | `contracts/intent-registry.json` | trigger description, intent-routing reference, Agent metadata, tests |
| Capability handoff | `contracts/capability-handoff.schema.json` and role requirements in `scripts/validate_runtime_payload.py` | calling spec, run manifest, capability template, tests |
| Run-specific machine state and transitions | `contracts/run-manifest.schema.json` and `scripts/validate_runtime_payload.py` | run-manifest template, calling spec, Markdown run-package views, tests |
| Style inventory | style-pack and legacy indexes | catalog, contact sheets, style-routing rules |
| Style candidate interaction | `contracts/style-selection.schema.json`, `references/style-library/style-match-rules.md`, and `scripts/validate_runtime_payload.py` | calling spec, question layer, style-selection and confirmation templates, Agent result, tests |
| Visual intent, media slots, source priority, and style sovereignty | `contracts/media-plan.schema.json`, `references/visual-intent-analysis.md`, and `scripts/validate_runtime_payload.py` | calling spec, question layer, media-plan template, media-generator adapters, production contract, QA, tests |
| Renderer behavior | adapter reference for that renderer | route registry, production contract, QA checks |
| Motion/video profiles and verification | `contracts/route-registry.json` and `references/motion-video-delivery.md` | invocation/result schemas, run manifest, confirmation, production route, QA, scripts, tests |
| In-slide choreography, final object-ID resolution, and grouped motion plans | `references/motion-video-delivery.md`, `scripts/resolve_pptx_motion_shape_ids.py`, and `scripts/apply_pptx_basic_motion.py` | calling spec, motion-plan template, outline, production route, QA, Agent metadata, tests |
| Visual QA, full-size previews, and collision gates | `CALLING_SPEC.md`, `scripts/verify_slide_previews.py`, and `scripts/verify_slide_collisions.py` | QA checklist, QA report, collision-rules template, Agent metadata, tests |

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
| Change a run state or transition | calling spec, result schema, run-manifest schema and template, runtime validator, confirmation and QA templates, tests |
| Change confirmation behavior | calling spec, question layer, user-confirmation template, tests |
| Change style scoring, eligibility, diversity, or candidate count | style-selection schema, runtime validator, style-match rules, style-pack visual families, style routing, question layer, confirmation/style-match templates, tests |
| Add or change a renderer | route registry, adapter reference, production contract, capability check, QA |
| Add or change motion/video behavior | route registry, motion-video reference, invocation/result schemas, run manifest, confirmation, production route, QA, capability/verification scripts, tests |
| Add or change grouped motion-plan behavior | motion-video reference, writer, motion-plan template, calling spec, outline, production route, QA, Agent metadata, tests |
| Add or change visual QA, preview, or collision behavior | calling spec, QA checklist/report, verification scripts, collision-rules template, Skill resource routing, Agent metadata, tests |
| Add or change source extraction | calling spec source normalization, adapter instructions, evidence fields, tests |
| Change intent classification | intent registry, intent-routing reference, trigger description, Agent metadata, tests |
| Change Agent/Skill handoff | handoff schema, runtime validator, calling spec, manifest, template, tests |
| Add or change visual-analysis or media-generation behavior | media-plan schema/template, runtime validator, visual-intent reference, adapter reference, calling spec, question layer, production contract, QA, tests |
| Add or update a style pack | pack directory, pack metadata, pack index, catalog, contact sheet, asset validation |
| Change output paths | calling spec, run manifest, production route, QA report, tests |
| Change a script dependency | script discovery logic, maintenance dependency notes, capability check, tests |

## Compatibility Rules

- Backward-compatible additions increment the minor version.
- Protocol `1.0` static invocations normalize to `1.1` with motion profile `none`; no compatibility conversion may infer motion or video.
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

## User-Reported Defect Loop

A user-reported defect is a maintenance input, not only an artifact revision request. Apply this loop whenever the reported behavior can be reproduced or represents a reusable failure mode:

1. Preserve the reported artifact, screenshot, error, or exact observation as evidence.
2. Reproduce and measure the failure with a minimal reproducer before changing behavior.
3. Classify it as a systemic defect or a run-specific preference. Structure, interaction, state, route, motion claims, output integrity, and QA failures are systemic when reproducible.
4. For a systemic defect, add a failing regression test before the fix.
5. Fix the current artifact when requested, then update the authority files and all dependent files listed by the source-of-truth table and change impact matrix.
6. Run the focused regression first, then full validation. Do not mark the maintenance event complete while either fails.
7. Report the measured root cause, changed Skill files, test evidence, and any capability that remains unverified.

An artifact-only fix is incomplete for a systemic defect. A subjective, run-specific aesthetic preference must not automatically become a global rule; record the classification and update the Skill only when the reusable failure mode can be stated and tested.

## Visual Intent Integration Maintenance Rule

Future changes to article analysis, image form, IP characters, generated media, or media-provider integration must preserve these invariants:

1. **Single-director ownership:** `guozhi-ppt-director` remains the only owner of story, page jobs, PPT style, route, confirmation, and QA. A child Skill supplies one declared capability and cannot reinterpret the request.
2. **Plan binding:** every media handoff binds the validated plan to the current request, run, and style through `media_plan_path` plus `media_plan_digest`. The handoff request and run must also match its manifest. A path string without readable content, matching identifiers, and digest verification is not sufficient.
3. **Generation scope:** `generation_scope: baseline_preview` is limited to one proposal slot and may run while confirmation is pending. `generation_scope: production_assets` requires confirmed or defaults-authorized `confirmation_status`.
4. **Style sovereignty:** image form and optional character identity may influence what is depicted. Every produced asset still uses the confirmed PPT style lock and `inherit_ppt_style`; an external skin never becomes deck art direction.
5. **Template media treatment:** real assets from the confirmed style pack define dimensionality, material, lighting, depth, photography/CGI/illustration method, crop, and scale. Missing subjects may use external analysis only under `visual_intent_only`; default hand-drawn output is forbidden unless the selected template or user explicitly requests it.
6. **Asset proof:** completed output maps one-to-one to requested slots and proves location, source type, PPT style lock, style transform, editable-text policy, provenance, and verification before renderer use.
7. **Dual invocation:** standalone Skill and parent-Agent execution use the same invocation, handoff, manifest, and result contracts. The host Agent executes tools and child-Skill calls; do not invent a direct Skill-to-Skill RPC mechanism. Human questions belong to the director in human mode or to the parent Agent in agent mode, never to a child provider.

When changing any invariant, first add a failing regression test, then synchronize `contracts/media-plan.schema.json`, `contracts/capability-handoff.schema.json`, `scripts/validate_runtime_payload.py`, `CALLING_SPEC.md`, the relevant adapter, QA, templates, examples, and Agent metadata. Treat omission of any layer as an incomplete modification.

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

For motion/video changes, also run `python3 scripts/check_motion_capabilities.py --json`, the `scripts/apply_pptx_basic_motion.py` writer tests, a focused `scripts/verify_pptx_motion.py` fixture test, the real-media `scripts/verify_video_asset.py` test when ffmpeg/ffprobe are available, and `scripts/verify_web_motion.mjs` when Playwright plus a browser are available. Playback reliability remains unverified when the declared target runtime is absent.

## Release Gate

The Skill is ready only when:

- all authority and dependent files use the same identifiers;
- no runtime document redefines a route, operation, or state;
- tests cover the changed behavior and pass;
- contract and Skill validators pass;
- required external capabilities are either verified or reported as unavailable;
- no generated caches, temporary downloads, secrets, or unrelated files are included.
