# Motion And Video Reliability Design

Date: 2026-07-11
Status: approved scope, implementation pending
Target protocol: 1.1

## Objective

Make motion and video explicit, machine-readable presentation capabilities. A run may claim motion or video delivery only when the selected renderer supports the requested profile and the required verification evidence exists.

The first release supports:

- browser motion with automated playback QA;
- PowerPoint 365 basic native motion: slide fade transitions and ordered object appear/fade builds;
- embedded or linked video in PPTX when the renderer and target PowerPoint support it;
- browser video playback in web decks;
- exported presentation video only through a renderer that can render and inspect the final media file.

WPS and Keynote are compatibility targets only. They are not covered by a PowerPoint reliability claim.

## Reliability Rule

`requested` is not the same as `verified`. The result must report one of these levels:

1. `declared`: a confirmed motion or video specification exists.
2. `structural`: the artifact contains the required OOXML or web structures and passes deterministic checks.
3. `playback`: the artifact was opened and played in the declared target runtime with evidence.

A native PowerPoint run that requires `playback` must return `blocked` when Microsoft PowerPoint is unavailable. It must not silently downgrade to a static deck or to `structural` verification.

## Profiles

### `none`

No motion is requested. Static route behavior remains backward compatible.

### `web_motion_v1`

Supports click/keyboard progression, ordered reveals, slide transitions, video playback, and browser-based QA. The renderer must provide a preview target and automated viewport/playback checks.

### `pptx_basic_v1`

Supports only:

- slide transition: `none` or `fade`;
- object entrance: `appear` or `fade`;
- trigger: `on_click`, `after_previous`, or `with_previous`;
- ordered build steps with stable object identifiers;
- optional video with explicit playback and audio policy.

Unsupported effects, missing object identifiers, or missing target-runtime verification produce `needs_input` or `blocked`. The adapter must not approximate an unsupported effect without confirmation.

### `dual_motion_v1`

Uses one shared story, style lock, page-job map, and semantic reveal order. The PPTX and HTML implementations may use different mechanics, but both must preserve facts and sequence. Each artifact receives independent verification evidence.

## Invocation Contract

Add optional `motion` and `video` objects under invocation constraints and run-manifest decisions. Invocation validation accepts protocol `1.0` and `1.1`. A `1.0` request is normalized to `1.1` with motion profile `none`; new result envelopes and run manifests use `1.1`. This is the only compatibility conversion and it cannot infer a motion request.

`motion` records:

- `requested`: boolean;
- `profile_id`: `none`, `web_motion_v1`, `pptx_basic_v1`, or `dual_motion_v1`;
- `playback_target`: `browser`, `powerpoint_365_windows`, or `powerpoint_365_macos`;
- `verification_required`: `structural` or `playback`;
- `advance`: `manual`, `timed`, or `mixed`;
- `reduced_motion_fallback`: boolean.

`video` records:

- `requested`: boolean;
- `delivery`: `embedded`, `linked`, `web`, or `rendered_video`;
- `playback`: `on_click`, `automatic`, or `poster_only`;
- `audio`: `muted` or `enabled`;
- `loop`: boolean;
- `poster_frame`: `auto` or an asset path;
- `fallback`: `poster`, `link`, or `blocked`.

Each video media slot records source path, MIME type, duration when available, trim range, slide/page ID, geometry, and checksum. URLs are source adapters, not playable assets, until downloaded or confirmed as links.

## Runtime Flow

1. Normalize motion language such as “动效展示”, “动画 PPT”, “带视频”, or “导出视频”.
2. Resolve route, motion profile, playback target, video policy, and required verification before confirmation.
3. Run renderer capability checks before planning concrete builds.
4. Freeze semantic reveal steps in layout contracts. Renderers may not invent additional animation.
5. Generate the artifact through the confirmed adapter.
6. Run structural validation.
7. Run target-runtime playback validation when required and available.
8. Complete only when the requested verification level is met; otherwise return `blocked` with the missing capability.

## Adapter Boundaries

### Web adapter

The web renderer owns browser mechanics. It must expose deterministic selectors or scene IDs for reveal steps and media slots. QA verifies initial, intermediate, and final states plus video readiness and playback events.

### Native PPTX adapter

The native adapter owns writing OOXML animation and media structures. It must preserve editable slide objects, notes, relationships, content types, and existing package integrity. It may use a verified renderer API, Microsoft PowerPoint automation, or a deterministic OOXML postprocessor.

The first implementation must include:

- environment capability inspection;
- PPTX package inspection for `p:transition`, `p:timing`, media parts, and relationships;
- a minimal fixture with a fade transition, two ordered builds, and one video slot;
- a machine-readable verification report.

PowerPoint automation is preferred for playback verification. Direct OOXML inspection is structural evidence only.

### Rendered-video adapter

An MP4/MOV export is a separate deliverable, not proof that a PPTX contains animation. The adapter must validate container/codec readability, duration, dimensions, frame activity, audio policy, and nonblank representative frames.

## Video Inputs Needed From The User Or Parent Agent

The minimum reliable input is the local video file or a downloadable source plus permission to retrieve it. Defaults reduce unnecessary questions:

- use the supplied clip without trimming unless a range is specified;
- generate the poster frame automatically;
- play on click in PPTX and automatically when the slide becomes active in HTML;
- keep audio enabled when the source contains speech, otherwise mute decorative loops;
- do not loop unless explicitly requested;
- use `poster` fallback when playback is optional and `blocked` when video is essential.

The only mandatory confirmation is a material conflict, such as an unavailable local file, a protected streaming URL, an unsupported codec, or a request for full PowerPoint playback verification without PowerPoint.

## Error Handling

- `MOTION_PROFILE_UNSUPPORTED`: renderer cannot implement the confirmed profile.
- `MOTION_TARGET_UNAVAILABLE`: required playback target is unavailable.
- `MOTION_STRUCTURE_INVALID`: expected transition/timing structures are missing or malformed.
- `VIDEO_SOURCE_UNAVAILABLE`: media cannot be resolved to an allowed local or linked source.
- `VIDEO_CODEC_UNSUPPORTED`: target runtime cannot support the media codec.
- `VIDEO_EMBED_FAILED`: package media part or relationship validation failed.
- `PLAYBACK_QA_FAILED`: playback evidence does not match the declared sequence or policy.

Retries may repair an adapter or source conversion failure without changing confirmed story, style, route, or motion semantics. Any route, profile, fallback, or delivery change requires confirmation.

## Testing And Release Gate

Regression tests must prove:

- protocol 1.0 calls without motion remain accepted and normalize to 1.1 with profile `none`;
- motion/video fields reject unknown values;
- a motion request cannot complete without profile and verification evidence;
- a structural PPTX fixture contains expected transitions, timing nodes, media parts, and relationships;
- playback-required runs block when the target runtime is missing;
- static PPTX, web, dual, and DashiAI routes retain their existing meaning;
- current style-preview interaction changes remain intact.

Release requires contract validation, unit tests, Skill validators, a minimal PPTX structural test, and a minimal browser motion/video test. PowerPoint playback support remains unavailable until a PowerPoint 365 environment produces recorded playback evidence.
