# Production Route

Machine source of truth: `run-manifest.json`

## Route Decision

- Protocol version:
- Request ID:
- Run ID:
- Route ID: native_pptx / web_deck / dual / dashiai / review_only
- Confirmed deliverable:
- Editability requirement:
- Motion profile: none / web_motion_v1 / pptx_basic_v1 / dual_motion_v1
- Choreography mode: transition_only / in_slide_grouped_v1 / web_scene_v1
- Motion-plan path: `motion-plan.json` / not applicable
- Final object-ID resolver: `scripts/resolve_pptx_motion_shape_ids.py` / not applicable
- In-slide choreography summary:
- Grouped builds and automatic sequence policy:
- `on_click` semantic checkpoints:
- Playback targets:
- verification_required: structural / playback
- Advance and reduced-motion policy:
- Video delivery / playback / audio / loop / poster / fallback:
- Capability check:
- Capability version:
- Capability status: available / missing / unverified
- Route confidence: high / medium / low

## Renderer Boundary

- Renderer or tool:
- Capability role: renderer
- Director decisions delegated: none
- Input package:
- Output directory:
- Temporary render directory:

## External Renderer Fields

- DashiAI project path, when route is `dashiai`:
- DashiAI theme:
- DashiAI theme ID:
- DashiAI goal path:
- DashiAI media intent:

## Expected Outputs

- Requested artifacts:
- Renderer outputs:
- Final checked artifacts:
- Full-size slide preview directory and expected slide count:
- Object-level layout directory, when available:
- Collision-rules path, when available:

## Verification Plan

- Confirm manifest state is `planned` before rendering.
- Confirm output paths are under the current run directory.
- Run renderer-specific validation and visual QA.
- Run `scripts/verify_slide_previews.py` and inspect every full-size slide preview; montage is navigation only.
- When object-level layout JSON exists, run `scripts/verify_slide_collisions.py` with run-specific surface rules.
- Record command, result, and evidence for every capability check.
- Run `scripts/check_motion_capabilities.py` before motion/video rendering.
- Validate the run-specific `motion-plan.json`; transition-only is insufficient unless explicitly confirmed.
- Confirm grouped builds keep every semantic visual unit together and use clicks only at semantic checkpoints.
- Confirm dynamic card/image requests use visible entrance variety and do not collapse to all-fade without a recorded compatibility reason.
- Resolve stable object names to final exported PPTX Shape IDs before applying native motion; pre-export picture/media IDs are not authoritative.
- Record whether the renderer wrote native structures or `scripts/apply_pptx_basic_motion.py` produced the motion artifact.
- Run `scripts/verify_pptx_motion.py` for `pptx_basic_v1` structural evidence.
- Run `scripts/verify_video_asset.py` for each local video and record media evidence.
- Run `scripts/verify_web_motion.mjs` for `web_motion_v1` playback evidence.
- Record playback evidence separately; structural evidence cannot satisfy a playback requirement.

## Failure Behavior

- Missing capability status: blocked
- Render or validation failure status: failed
- Route changes require explicit approval; no silent fallback.
- Missing playback target code: `MOTION_TARGET_UNAVAILABLE`; do not downgrade `verification_required`.
