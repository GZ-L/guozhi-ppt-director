# User Confirmation

Machine source of truth: `run-manifest.json`

## Invocation

- Protocol version:
- Request ID:
- Run ID:
- Operation:
- Interaction mode: human / agent
- Source material:

## Recommended Complete Configuration

Style choice uses `style_candidates`: three eligible style candidates, one recommended candidate, and two visual alternatives. `recommended_style_id` is deterministic and never random. Every row requires a visible Preview asset.

- Exact page count:
- Speaking time:
- Deliverable:
- Route ID:
- Recommended style ID / `recommended_style_id`:
- DashiAI theme ID, when route is `dashiai`:
- Style category:
- Visual traits:
- Preview asset:
- Preview displayed: yes / no
- Rewrite boundary:
- Speaker notes: yes / no
- Citations: yes / no
- Motion requested: yes / no
- Motion profile: none / web_motion_v1 / pptx_basic_v1 / dual_motion_v1
- Choreography mode: transition_only / in_slide_grouped_v1 / web_scene_v1 / dual_grouped_v1
- In-slide motion intent: cards / diagrams / product parts / conclusions / not applicable
- Motion intensity: subtle / dynamic / reduced-motion
- Visual media intent: authorized source images / product screenshots / generated visuals / none
- Sequence policy: automatic after_previous / speaker-controlled semantic checkpoints / mixed
- Playback targets:
- verification_required: structural / playback
- Advance mode: manual / timed / mixed
- Reduced-motion fallback: yes / no
- Video requested: yes / no
- Video delivery / playback / audio / loop / poster / fallback:
- Recommendation evidence:
- Primary risk:

## Style Candidates / `style_candidates`

| Rank | Role | Style ID | Name | Category | Visual family | Fit score | Repeat penalty | Fit evidence | Preview asset | Displayed |
| ---: | --- | --- | --- | --- | --- | ---: | ---: | --- | --- | --- |
| 1 | recommended |  |  |  |  |  |  |  |  | yes |
| 2 | visual alternative |  |  |  |  |  |  |  |  | yes |
| 3 | visual alternative |  |  |  |  |  |  |  |  | yes |

## Unresolved Fields

- None, or list exact field names from the manifest:

## Confirmation

- Status: pending / confirmed / defaults_authorized
- Exact confirmation text:
- Confirmed at:
- Fields changed after recommendation:

## Proceed Gate

- Manifest state:
- Rendering is permitted only when the manifest is `confirmed` and later `planned`.
- Motion/video rendering is permitted only after the selected route passes `scripts/check_motion_capabilities.py` for the confirmed profile and verification level.
- A general animation request confirms in-slide choreography; transition-only output is valid only when the user explicitly requests page transitions only.
