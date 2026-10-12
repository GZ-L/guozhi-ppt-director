# QA Checklist

Use before saying a presentation package is ready.

## Logic

- The deck has one clear thesis.
- Every page supports the thesis.
- The page order creates a visible argument.
- The opening explains why the audience should care.
- The close gives a next action, takeaway, or decision.

## Slide Density

- One main message per page.
- No page is used as a document dump.
- Speaker notes hold details that do not belong on the slide.
- Titles say the point, not just the topic.

## Visual Quality

- `media-plan.json` passes runtime validation before any media-generation handoff.
- Every media handoff binds `media_plan_path` to `media_plan_digest` and the current request, run, and PPT style lock.
- Every capability handoff uses the same request and run as its manifest; production media is not recorded before manifest confirmation.
- `baseline_preview` requests contain exactly one slot. `production_assets` requests have confirmed or defaults-authorized `confirmation_status`.
- Completed media assets map one-to-one to requested slots and include source, style inheritance, editable-text policy, provenance, location, and verified asset proof.
- The PPT style lock is authoritative; every generated or transformed slot records `inherit_ppt_style`, and no external IP skin changes the deck palette, typography, line work, texture, lighting, or composition rhythm.
- The template media treatment is authoritative: every generated fallback was compared against declared `media_treatment_references` for dimensionality, material, lighting, depth, photography/CGI/illustration method, crop, and scale.
- A hand-drawn fallback appears only when the confirmed template is hand-drawn or the user explicitly requested it. Missing subjects use `visual_intent_only`; they do not inherit the adapter's drawing style.
- Authorized source media and native PPT structures were evaluated before generated visuals; the selected image form solves the recorded reader block.
- Optional IP or custom characters have explicit user or parent-Agent confirmation and were rendered in the PPT style rather than their source skin.
- Style is consistent across cover, section pages, body pages, and closing page.
- Alignment, spacing, and hierarchy are intentional.
- Colors are not one-note unless the brief requires strict branding.
- Screenshots, charts, and diagrams are readable.
- One full-size slide preview exists for every page and passes `scripts/verify_slide_previews.py`; 16:9 output is at least 1280x720.
- Every full-size slide preview was inspected at readable scale. A montage is navigation only and is not collision, clipping, or typography evidence.
- When object-level layout JSON exists, run-specific surface rules exist and collision verification passes with `scripts/verify_slide_collisions.py`.
- Visual QA records the renderer and the visual production method used to create editable elements, images, diagrams, and previews.
- Requested source images, screenshots, charts, or generated visuals are content-bearing, readable, attributed, and not generic filler; editable titles, captions, conclusions, and surrounding card geometry remain editable.

## Route Fit

- `run-manifest.json` is the machine source of truth, conforms to `contracts/run-manifest.schema.json`, and records protocol version, request ID, run ID, operation, route, state, and append-only state history.
- `scripts/validate_runtime_payload.py --kind manifest` passes before state promotion and delivery.
- Rendering started only after states `confirmed` and `planned`.
- PPTX route: text and shapes should be editable where possible.
- Visual web route: motion helps comprehension, not decoration only.
- Dual route: both versions share the same story and style.
- Route `dashiai`: route, theme, media intent, and install state were explicitly confirmed before production.
- Route `dashiai`: DashiAI was used only as renderer/template engine after the Guozhi director package was complete.
- The user confirmation gate was satisfied before final production.
- No second PPT Skill was used as a separate director.

## Motion And Video Fit

- Requested motion has an exact profile ID and `verification_required` value.
- A run-specific `motion-plan.json` records in-slide choreography, motion jobs, grouped builds, stable IDs, triggers, effects, and durations.
- Transition-only is insufficient for a general animation request; at least one content slide contains verified object builds unless the user explicitly requested transitions only.
- Automatic sequences use `after_previous`; `on_click` is reserved for semantic checkpoints.
- Card backgrounds, accents, titles, and copy that form one visual unit share one motion group instead of animating as unrelated fragments.
- Images, frames, and captions that form one visual unit share one group. General dynamic card or image requests normally use three to five semantic beats per content slide and at least two visible entrance families across the deck; all-fade output requires an explicit compatibility or reduced-motion reason.
- Every animated object has a unique stable name, and final `shape_ids` were produced by `scripts/resolve_pptx_motion_shape_ids.py` against the exported clean PPTX. Pre-export layout IDs are not accepted as picture/media evidence.
- The route registry declares the selected profile and video delivery.
- `scripts/check_motion_capabilities.py` output is recorded before rendering.
- When used, `scripts/apply_pptx_basic_motion.py` wrote a distinct output and reported only supported slide/build targets.
- `pptx_basic_v1` structural claims include a passing `scripts/verify_pptx_motion.py` report.
- `web_motion_v1` playback claims include a passing `scripts/verify_web_motion.mjs` report for initial, intermediate, final, reduced-motion, and requested video states.
- `dual_motion_v1` has separate PPTX and HTML verification records.
- `verification_required: playback` is not downgraded when the target runtime is missing; return `MOTION_TARGET_UNAVAILABLE` and `blocked`.
- Embedded/linked video has a valid source, playback/audio/loop/poster/fallback policy, and relationship or browser-event evidence.
- Every local video has a passing `scripts/verify_video_asset.py` report before renderer handoff.
- Exported video is checked for readable metadata, duration, dimensions, nonblank frames, activity, and audio policy.
- Profile `none` is delivered with the exact disclosure `Static PPTX, no animation`.
- Motion delivery distinguishes structural verification from playback verification; screenshots and preview images are not playback evidence.

## Style Library Fit

- The selected references match topic, audience, density, and route.
- The style mode is explicit: Style Library Replica.
- If a style pack is available, output slide roles map to pack roles instead of repeatedly copying the cover.
- If the selected reference is cover-only, the limitation is recorded and accepted before production.
- The deck visibly matches the primary reference's palette, typography mood, spacing, composition rhythm, shape vocabulary, image treatment, and density.
- The deck replicates style instead of copying source content, logos, characters, products, people, exact artwork, or page-specific compositions.
- The fidelity lock is recorded: primary reference, match closely, do not copy, extension method, and allowed director freedom.
- The final style system works for cover, body, diagrams, and closing pages.

## DashiAI Adapter Fit

- Route `dashiai` was selected explicitly.
- `scripts/check_dashiai_adapter.py` was run and recorded.
- The chosen DashiAI theme matches topic, audience, density, and media needs.
- Final DashiAI slides use concrete `layout + props`, not draft-only `role`.
- DashiAI `goal.json` is under the deck output folder, not inside the DashiAI Skill.
- DashiAI validations ran: goal spec, rendered deck, default-copy check, and export check when requested.
- DashiAI output has no unrelated default template copy.
- Missing DashiAI install or export failures were reported instead of silently switching route.

## Delivery

- Final state is `completed` only when every requested artifact exists and is checked.
- Final file names are clear.
- Source notes or links are preserved.
- Known limitations are listed.
- Next revision suggestions are concrete.
- A collision or preview-resolution failure prevents state `completed` until a corrected artifact passes the same check.
