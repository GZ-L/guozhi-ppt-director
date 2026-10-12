# Motion And Video Delivery

Use this reference only after `CALLING_SPEC.md`. Route identifiers remain owned by `contracts/route-registry.json`.

## Reliability Model

Motion and video have three evidence levels:

- `declared`: the confirmed specification exists;
- `structural`: the artifact contains the required package or web structures and passes deterministic checks;
- `playback`: the declared target runtime played the result and produced evidence.

The invocation field `verification_required` is a completion gate. A run cannot silently replace `playback` with `structural`.

## Profiles

### `none`

Static output. A protocol `1.0` invocation normalizes to this profile.

### `web_motion_v1`

Supports browser slide transitions, ordered reveals, click/keyboard progression, reduced-motion fallback, and web video playback. The renderer exposes stable scene/build/media IDs. Playback QA checks initial, intermediate, and final states plus video readiness/play events.

The web artifact must expose `window.__GUOZHI_DECK_QA__` with version, `getState()`, and `advance()` methods. Run `scripts/verify_web_motion.mjs --url <preview> --expect-builds <count> --expect-video --json`; omit `--expect-video` when no video is requested. Supply `--browser-executable` when Playwright has no bundled browser.

### `pptx_basic_v1`

Supports only:

- slide transition `none` or `fade`;
- object entrance `appear`, `fade`, directional `wipe_*`, or directional `slide_from_*`;
- trigger `on_click`, `after_previous`, or `with_previous`;
- stable slide and shape IDs;
- embedded or linked video with a confirmed playback policy.

#### In-Slide Choreography

When the user asks for animation, dynamic cards, diagram reveals, product-part reveals, or motion inside a page, use `choreography_mode: in_slide_grouped_v1`. Transition-only is insufficient unless the user explicitly limits the request to page transitions.

Create `motion-plan.json` from `templates/motion-plan.json`. A general animation request uses three to five semantic beats per content slide and may use up to six when the explanation genuinely needs them. Every animated slide records one `motion_job` and one or more grouped builds. Each group contains:

- a stable `group_id` and semantic intent;
- stable `shape_names` plus the final exported `shape_ids` for every object in one visual unit, such as card background, accent, title, copy, image, and caption;
- one supported effect and duration;
- `after_previous` for automatic explanatory sequences or `on_click` at semantic checkpoints.

The writer expands the first object in a group with the declared trigger and all remaining group objects with `with_previous`, so the unit enters together. Do not animate decorative elements independently when they belong to the same semantic unit. A motion-requested deck may use transition-only slides for covers or separators, but at least one content slide must contain in-slide grouped choreography.

For dynamic card or image requests, all-fade choreography is insufficient unless reduced motion or the confirmed playback target requires it. Use at least two entrance families across the deck, normally `slide_from_*` for cards or images and `wipe_*` for connectors or conclusions, while keeping `fade` for soft supporting evidence. Motion must clarify sequence, comparison, or hierarchy rather than make every small object move.

Pre-export layout IDs are not authoritative for PPTX pictures or media. Name every animated object, export the clean PPTX, run `scripts/resolve_pptx_motion_shape_ids.py --pptx <static.pptx> --plan <motion.json> --output <resolved.json>`, and only then apply motion. Missing or duplicate names are a blocking `MOTION_TARGET_RESOLUTION_FAILED`; never fall back to stale layout IDs.

Run `python3 scripts/check_motion_capabilities.py --require-profile pptx_basic_v1 --verification <structural|playback>`. If the native renderer does not write the supported structures, resolve final IDs and run `python3 scripts/apply_pptx_basic_motion.py --input <static.pptx> --plan <resolved.json> --output <animated.pptx>`. The writer accepts legacy object builds and `in_slide_grouped_v1`, and refuses unsupported effects, invalid groups, duplicate or missing shape IDs, source/output path reuse, and slides with existing timing or transition structures. After rendering, run `python3 scripts/verify_pptx_motion.py --pptx <file> --expect-transition --expect-build` and add `--expect-video` when required.

## Visual Asset Choreography

When the user asks for pictures, richer cards, or a livelier deck, assign two to four content-bearing media slots across a short deck before rendering. Prefer authorized source images, product screenshots, charts, or diagrams; generate a new bitmap only when the source has no suitable visual. Do not add generic filler imagery. Every image must remain readable at full-slide scale, keep source attribution, and sit inside a layout role that still preserves editable titles, captions, conclusions, and surrounding card geometry. Animate an image with its frame and caption as one semantic group.

OOXML inspection proves structure only. PowerPoint playback evidence requires Microsoft PowerPoint 365 for the declared operating system. Keynote and WPS are compatibility targets, not substitutes.

### `dual_motion_v1`

Uses one story, style lock, page-job map, and semantic reveal order. The PPTX and HTML mechanics may differ, but facts and sequence must remain aligned. Each artifact has separate verification records.

## Video Policy

Every requested video records:

- delivery: `embedded`, `linked`, `web`, or `rendered_video`;
- playback: `on_click`, `automatic`, or `poster_only`;
- audio: `muted` or `enabled`;
- loop: boolean;
- poster frame: `auto` or an asset path;
- fallback: `poster`, `link`, or `blocked`.

Each media slot records source path or approved URL, MIME type, duration when available, trim range, page ID, geometry, and checksum. A streaming or protected URL is not an embedded asset until a source adapter produces an authorized local file.

Run `python3 scripts/verify_video_asset.py --video <file> --json` for every local video before rendering. Record codec, duration, dimensions, audio streams, and SHA-256 in the normalized asset. A package relationship or file extension alone is not sufficient media evidence.

Defaults when no material conflict exists:

- use the full clip;
- generate a poster automatically;
- play on click in PPTX and when the scene becomes active in HTML;
- preserve speech audio and mute decorative loops;
- do not loop;
- use poster fallback when optional and `blocked` when essential.

## Rendered Video

An exported MP4/MOV is a separate deliverable and does not prove that a PPTX contains animation. Verify readable container/codec metadata, duration, dimensions, representative nonblank frames, frame activity, and requested audio policy with available media tools.

## Errors

- `MOTION_PROFILE_UNSUPPORTED`: selected renderer cannot implement the profile.
- `MOTION_TARGET_UNAVAILABLE`: required playback target is unavailable.
- `MOTION_STRUCTURE_INVALID`: transition, timing, target, or web scene evidence is invalid.
- `VIDEO_SOURCE_UNAVAILABLE`: source cannot be resolved under the confirmed policy.
- `VIDEO_CODEC_UNSUPPORTED`: target runtime does not support the media codec.
- `VIDEO_TOOL_UNAVAILABLE`: required `ffprobe` media inspection is unavailable.
- `VIDEO_EMBED_FAILED`: media part or relationship validation failed.
- `PLAYBACK_QA_FAILED`: playback evidence differs from the confirmed sequence or policy.

Changing route, profile, delivery, or fallback requires confirmation. Repairing the same adapter or converting an authorized source to a supported codec does not change presentation decisions.
