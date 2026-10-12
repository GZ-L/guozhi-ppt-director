# Xiaohu IP Studio Adapter

Use Xiaohu IP Studio only as an optional `media_generator` capability for article analysis, visual-anchor selection, image form planning, and asset generation. It is not a PPT director, renderer, style library, or source of default characters. The PPT style lock is authoritative, the template media treatment is authoritative, and the adapter is restricted to `visual_intent_only` when fallback subjects are needed. It never changes the deck style.

Upstream project: [xiaohuailabs/xiaohu-ip-studio](https://github.com/xiaohuailabs/xiaohu-ip-studio). Keep it external and respect its license and notice when installed or redistributed. This Skill does not copy its role library, skins, prompts, or bitmap assets.

## Capability Boundary

Input:

- validated `media-plan.json`;
- matching `media_plan_digest`, `request_id`, and `run_id`;
- confirmed `style_lock` and relevant style-board evidence;
- real `media_treatment_references` from the confirmed style pack;
- only the declared `media_slots` and authorized source assets;
- target slot ratio and safe crop area.
- `generation_scope`: `baseline_preview` or `production_assets`.

Output:

- generated or transformed assets keyed by `slot_id`;
- prompt/provenance record;
- dimensions, crop behavior, and generation status;
- one-to-one asset proof containing location, source type, PPT style lock, `inherit_ppt_style`, `editable_ppt_text`, provenance, and verified status.

The adapter may use an emotion anchor, explanatory diagram, comic, overview, evidence image, process, comparison, relationship, timeline, or physical-metaphor image form. It may not import an independent palette, illustration skin, type treatment, texture, character rendering style, or page composition. If the template uses 3D CGI, glass, metal, cinematic photography, or dimensional interface objects, the adapter output must use that same treatment instead of its own hand-drawn default.

## Call Order

1. The director normalizes sources and produces a provisional visual-needs summary.
2. The director runs the normal three-style recommendation flow.
3. If a character is proposed, keep the run in `needs_input`. After the user selects an exact PPT style, write and validate a provisional `media-plan.json`, bind it with `media_plan_digest`, then request exactly one slot with `generation_scope: baseline_preview`.
4. The parent interaction shows the baseline and obtains explicit character approval. The baseline is proposal evidence, not deck rendering.
5. Freeze the complete confirmation, lock the PPT style, and write the final `media-plan.json`.
6. Validate the final plan with `--kind media_plan`.
7. Send a `media_generator` handoff containing the exact `media_slots`, `generation_scope: production_assets`, and director context containing `media_plan_path`, `media_plan_digest`, `confirmation_status`, and the locked style.
8. Generate remaining assets only after the baseline passes style, factual, crop, and text-editability checks. Without a character proposal, generate one baseline asset before any costly batch.
9. Insert assets into the renderer package, keep surrounding text editable, and map motion groups to the image, frame, caption, and explanatory labels as one semantic unit.

## Style Conflict Rule

For every asset, convert image form and character identity into the confirmed PPT visual language using `inherit_ppt_style` and the recorded template media treatment. If the incoming IP skin conflicts, preserve only the subject relationship or pose needed by the explanation and redraw the visual with the template's dimensionality, material, lighting, depth, crop, and image method. If that still conflicts, drop the character and keep a non-IP explanatory visual. Never modify the PPT style lock to match the adapter.

## Failure And Fallback

- Missing adapter: use authorized source media or native PPT visuals; record the unavailable capability.
- Missing character confirmation: return `needs_input` to the parent; do not generate the character.
- A `production_assets` request with pending confirmation is invalid. Do not reinterpret it as authorized.
- A plan path, digest, request, run, or style mismatch is invalid. Do not read another run's plan.
- Returned assets without one-to-one slot mapping and complete asset proof are invalid and never reach the renderer.
- Style drift: reject and retry under the same lock once.
- Raster text: remove it and rebuild text as editable PPT objects.
- Unverifiable or generic output: reject it and use the next allowed asset class.
- Adapter failure after generation starts: preserve evidence, mark the handoff `failed`, and do not claim the deck is complete until a confirmed fallback is rendered and checked.
