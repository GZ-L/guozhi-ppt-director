# Motion And Video Reliability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Add machine-readable, capability-gated, and verifiable motion and video delivery to `guozhi-ppt-director` without changing existing route identifiers or weakening static-deck behavior.

**Architecture:** Protocol 1.1 adds optional motion/video decisions while accepting protocol 1.0 static invocations. A focused capability checker discovers available playback and media tools; a separate OOXML inspector verifies PPTX transitions, timing targets, and embedded media. Runtime documents require the requested verification level before completion and block unsupported delivery instead of silently downgrading.

**Tech Stack:** Python 3 standard library (`argparse`, `json`, `zipfile`, `xml.etree.ElementTree`, `subprocess`, `shutil`), JSON Schema documents, Markdown runtime contracts, `unittest`.

## Global Constraints

- Keep route IDs `native_pptx`, `web_deck`, `dual`, `dashiai`, and `review_only` unchanged.
- Accept invocation protocol `1.0` and `1.1`; normalize new run manifests and results to `1.1`.
- Support `web_motion_v1`, `pptx_basic_v1`, and `dual_motion_v1`; do not imply support for arbitrary PowerPoint effects.
- PowerPoint playback verification requires Microsoft PowerPoint 365 and must block when unavailable.
- WPS and Keynote are compatibility targets only.
- Preserve current uncommitted style-preview interaction changes.
- Add no required third-party Python dependency.

---

### Task 1: Protocol 1.1 Motion And Video Contracts

**Files:**
- Modify: `tests/test_contract.py`
- Modify: `contracts/invocation.schema.json`
- Modify: `contracts/result.schema.json`
- Modify: `contracts/route-registry.json`
- Modify: `templates/run-manifest.json`
- Modify: `scripts/validate_contract.py`

**Interfaces:**
- Consumes: existing route IDs and operation/state enums.
- Produces: `motion` and `video` decision objects; route `motion_profiles` and `video_deliveries`; result `verification` evidence array.

- [x] **Step 1: Add failing contract tests**

Add tests that assert input versions are `{"1.0", "1.1"}`, manifest/result version is `1.1`, motion profile enums are exact, route capabilities are declared, and a legacy 1.0 invocation without motion remains structurally valid.

- [x] **Step 2: Run the focused tests and verify RED**

Run: `python3 -m unittest tests.test_contract.ContractTests.test_motion_video_contracts -v`

Expected: FAIL because motion/video properties and protocol 1.1 are absent.

- [x] **Step 3: Add the minimum synchronized schema changes**

Use these stable enums:

```text
motion.profile_id = none | web_motion_v1 | pptx_basic_v1 | dual_motion_v1
motion.playback_targets[] = browser | powerpoint_365_windows | powerpoint_365_macos
motion.verification_required = structural | playback
video.delivery = embedded | linked | web | rendered_video
verification.level = declared | structural | playback
```

Route registry capabilities must match route meaning: `native_pptx` permits `none,pptx_basic_v1`; `web_deck` permits `none,web_motion_v1`; `dual` permits `none,dual_motion_v1`; DashiAI declares only capabilities its adapter can prove; `review_only` permits `none`.

- [x] **Step 4: Run the focused test and validator**

Run: `python3 -m unittest tests.test_contract.ContractTests.test_motion_video_contracts -v && python3 scripts/validate_contract.py`

Expected: PASS and validator reports protocol 1.1 consistency.

### Task 2: Environment Capability Inspection

**Files:**
- Create: `scripts/check_motion_capabilities.py`
- Modify: `tests/test_contract.py`

**Interfaces:**
- Produces CLI JSON with `powerpoint`, `keynote`, `ffprobe`, `ffmpeg`, `browser_renderer`, and supported verification levels.
- Exit `0` when inspection succeeds, regardless of optional application availability; malformed arguments exit nonzero.

- [x] **Step 1: Add failing capability-check tests**

Test `inspect_capabilities()` with injected executable/application probes and assert that absent PowerPoint removes `playback` from `pptx_basic_v1` but leaves `structural` available.

- [x] **Step 2: Run the test and verify RED**

Run: `python3 -m unittest tests.test_contract.MotionCapabilityTests -v`

Expected: ERROR because the module does not exist.

- [x] **Step 3: Implement deterministic inspection**

Discover executables with `shutil.which`; detect macOS applications under `/Applications` and `$HOME/Applications`; emit absolute paths only as runtime evidence, never as committed defaults. `--require-profile pptx_basic_v1 --verification playback` exits `2` with error code `MOTION_TARGET_UNAVAILABLE` when PowerPoint is absent.

- [x] **Step 4: Run tests and inspect local output**

Run: `python3 -m unittest tests.test_contract.MotionCapabilityTests -v && python3 scripts/check_motion_capabilities.py --json`

Expected: tests pass; local JSON reports Keynote present and PowerPoint absent.

### Task 3: PPTX Structural Motion And Video Verification

**Files:**
- Create: `scripts/verify_pptx_motion.py`
- Create: `tests/fixtures/pptx-motion/README.txt`
- Modify: `tests/test_contract.py`

**Interfaces:**
- `inspect_pptx(path: Path) -> dict` returns slide count, transition slides, timing slides, targeted shape IDs, media parts, media relationships, errors, and verification level.
- CLI accepts `--pptx`, `--expect-transition`, `--expect-build`, `--expect-video`, and `--json`.

- [x] **Step 1: Add failing package-inspection tests**

Build tiny PPTX ZIP fixtures in test setup using standard-library XML strings. Assert detection of `p:transition`, `p:timing`, `p:spTgt`, `a:videoFile`, media relationships, missing targets, and malformed ZIP input.

- [x] **Step 2: Run the test and verify RED**

Run: `python3 -m unittest tests.test_contract.PptxMotionVerificationTests -v`

Expected: ERROR because `verify_pptx_motion.py` does not exist.

- [x] **Step 3: Implement the read-only verifier**

Parse ZIP entries and namespaces without rewriting the package. Validate that every targeted shape ID exists on its slide, every embedded media relationship resolves to a package part, and every requested expectation has evidence. Emit stable error codes `MOTION_STRUCTURE_INVALID` and `VIDEO_EMBED_FAILED`.

- [x] **Step 4: Run tests and verify an existing static deck**

Run: `python3 -m unittest tests.test_contract.PptxMotionVerificationTests -v`

Then run the CLI against the latest WorkBuddy deck with `--expect-transition`; expected result is a nonzero structural failure because the current deck has no transitions.

### Task 4: Runtime Rules, Confirmation, And QA Synchronization

Before this task, implement `scripts/apply_pptx_basic_motion.py` with a failing-test cycle. The adapter consumes a JSON plan containing slide number, `fade` transition, and ordered `appear`/`fade` builds targeted by existing shape IDs. It must preserve the source package, reject unsupported effects or existing timing trees, write to a distinct output, and pass `scripts/verify_pptx_motion.py`. This is the structural writer for `pptx_basic_v1`; it does not claim playback verification.

**Files:**
- Modify: `SKILL.md`
- Modify: `CALLING_SPEC.md`
- Modify: `OVERVIEW.md`
- Modify: `README.md`
- Modify: `references/output-routes.md`
- Create: `references/motion-video-delivery.md`
- Modify: `references/director-production-contract.md`
- Modify: `references/qa-checklist.md`
- Modify: `references/question-layer.md`
- Modify: `templates/user-confirmation.md`
- Modify: `templates/production-route.md`
- Modify: `templates/outline.md`
- Modify: `templates/qa-report.md`
- Modify: `MAINTENANCE_SPEC.md`
- Modify: `tests/test_contract.py`

**Interfaces:**
- Consumes: protocol fields and script error codes from Tasks 1-3.
- Produces: one authoritative call order for detecting, confirming, rendering, and verifying motion/video.

- [x] **Step 1: Add failing documentation synchronization tests**

Assert that authority/dependent documents contain `pptx_basic_v1`, `verification_required`, `MOTION_TARGET_UNAVAILABLE`, `scripts/check_motion_capabilities.py`, and `scripts/verify_pptx_motion.py`; assert no document claims generic “all PowerPoint animation” support.

- [x] **Step 2: Run test and verify RED**

Run: `python3 -m unittest tests.test_contract.ContractTests.test_motion_runtime_docs_are_synchronized -v`

Expected: FAIL on missing runtime terms.

- [x] **Step 3: Update runtime and maintenance documents**

Require motion profile, playback targets, video policy, and verification level before confirmation when requested. Require renderer capability checks before planning. Keep HTML and PPTX verification separate in dual runs. Document user inputs and defaults without adding an unnecessary question menu.

- [x] **Step 4: Run focused and complete unit tests**

Run: `python3 -m unittest tests.test_contract.ContractTests.test_motion_runtime_docs_are_synchronized -v && python3 -m unittest discover -s tests -p 'test_*.py' -v`

Expected: PASS.

### Task 5: End-To-End Validation And Release Evidence

**Files:**
- Modify: `scripts/validate_contract.py`
- Modify: `examples/REAL_CASES.md`
- Modify: `docs/superpowers/plans/2026-07-11-motion-video-reliability.md`

**Interfaces:**
- Produces: validation output proving protocol consistency and local capability state; records one realistic Agent motion request and one video request.

- [x] **Step 1: Add validator checks for scripts and route capabilities**

Validator must reject missing scripts, unknown profiles, incompatible route/profile pairs, or schema/manifest version drift.

- [x] **Step 2: Add realistic interaction cases**

Include a `dual_motion_v1` request and a `pptx_basic_v1` playback request that becomes `blocked` when PowerPoint is unavailable. Do not claim a rendered PowerPoint fixture was playback verified.

- [x] **Step 3: Run all required validators**

Run:

```bash
python3 scripts/validate_contract.py
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 "$HOME/.codex/skills/standard-skill-maker/scripts/validate_skill.py" .
python3 "$HOME/.codex/skills/.system/skill-creator/scripts/quick_validate.py" .
python3 scripts/check_motion_capabilities.py --json
```

Expected: all validators and tests pass; capability output explicitly reports PowerPoint playback unavailable on this machine.

- [x] **Step 4: Inspect diff and commit only intended changes**

Run: `git diff --check && git status --short && git diff --stat`

Confirm current style-preview modifications remain present and no style assets, credentials, caches, or unrelated generated files were added.
