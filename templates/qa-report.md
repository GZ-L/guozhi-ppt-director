# QA Report

## Summary

- Run state: qa / completed / blocked / failed
- QA result: pass / needs revision / blocked
- Route checked:
- Protocol version:
- Request ID:
- Run ID:
- Operation:
- Run package directory:
- Final output directory:
- Files checked:
- Failed gate: none / confirmation / brief / story / style / route / production / QA
- Return to stage:
- DashiAI route checked: yes / no / not applicable
- DashiAI validation checked: yes / no / not applicable
- Motion profile:
- Choreography mode:
- Motion-plan path and validation:
- In-slide group count, stable object names, and resolved final Shape IDs:
- Entrance effect families used and any all-fade compatibility reason:
- verification_required:
- Motion capability report:
- PPTX structural verification report:
- Playback targets and evidence:
- Video policy and verification evidence:
- Renderer and visual production method:
- Full-size slide preview directory, count, and minimum resolution:
- Collision verification rules and report:

## Artifact Check

- [ ] Run package exists under `outputs/<deck-slug>/<run-id>/director-package/` or a user-confirmed output root
- [ ] `run-manifest.json` exists and is the machine source of truth
- [ ] Manifest passes `scripts/validate_runtime_payload.py --kind manifest`
- [ ] `state_history` starts at `received`, contains only allowed transitions, and ends at the manifest status
- [ ] Source files in `templates/` were not filled as run artifacts
- [ ] `user-confirmation.md`
- [ ] `deck-brief.md`
- [ ] `outline.md`
- [ ] `style-match.md` when style references are used
- [ ] `style-board.md`
- [ ] `production-route.md`
- [ ] Final artifact or complete director package
- [ ] `qa-report.md`

## Story QA

- Thesis clarity:
- Slide order:
- Opening:
- Closing:
- Issues:

## Motion And Video QA

- Transition-only request explicitly confirmed: yes / no / not applicable
- In-slide choreography and grouped builds match `motion-plan.json`:
- Named motion targets were resolved against the exported clean PPTX:
- Requested source images/screenshots/generated visuals are readable, attributed, and content-bearing:
- Automatic sequences and semantic checkpoints match the confirmed policy:
- Route/profile compatibility:
- Capability check command and result:
- Structural verification level and evidence:
- Playback verification level and evidence:
- Video source/codec/package or browser-event evidence:
- `MOTION_TARGET_UNAVAILABLE` or other blocking code, when applicable:
- Issues:

## Visual QA

- Full-size slide preview verification command and result:
- Every full-size slide preview inspected at readable scale: yes / no
- Montage is navigation only and was not used as sole QA evidence: yes / no
- Collision verification command, rules, report, and result:
- Renderer and visual production method:
- Hierarchy:
- Spacing and alignment:
- Color:
- Typography:
- Images/screenshots:
- Charts/diagrams:
- Style mode and fidelity:
- Issues:

## Route QA

- Selected route matches the confirmed deliverable:
- If PPTX is required, editability is preserved where possible:
- If a visual web deck is required, preview/render path is clear:
- Dual route alignment:
- Route `dashiai` confirmed before production:
- DashiAI install state checked:
- DashiAI theme and media intent recorded:
- DashiAI goal/spec validation passed:
- DashiAI default-copy check passed:
- DashiAI export checked:
- No second PPT Skill used as a separate director:
- Issues:

## Required Fixes

1.
2.
3.

## Known Limitations

-

## Delivery Disclosure

- Static profile: `Static PPTX, no animation`
- Motion profile and structural verification:
- Playback verification target and evidence:

## Next Revision Suggestions

-
