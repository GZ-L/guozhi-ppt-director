# Visual Intent Analysis

Use this reference after source normalization to decide where a slide needs a visual and what cognitive work that visual must perform. It defines image form, not an independent art direction. The PPT style lock is authoritative.

## Output Contract

After confirmation and style locking, write `director-package/media-plan.json` from `templates/media-plan.json` and validate it with:

```bash
python3 scripts/validate_runtime_payload.py --kind media_plan --input <media-plan.json>
```

Every slot records the reader block, visual job, hero thesis, must-show facts, source priority, image form, slot geometry, optional character decision, editable-text policy, and motion intent. The plan records real style-pack image assets as `media_treatment_references`, uses `fallback_image_form_policy: visual_intent_only`, and every slot uses `style_transform: inherit_ppt_style`.

## Analysis Sequence

For each planned slide:

1. State the slide's rhetorical job and one-sentence hero thesis.
2. Identify the reader block: abstraction, comparison burden, process complexity, relationship ambiguity, evidence trust, or emotional distance.
3. Decide whether a visual materially reduces that block. Use `visual_need: false` when text or native structure is clearer.
4. List only facts or relationships that the visual must show. Do not place decorative concepts in `must_show`.
5. Select the first viable asset class in this order: authorized source, product screenshot, native PPT diagram/chart, generated visual.
6. Select one image form: evidence, process, comparison, relationship, timeline, overview, comic, or physical metaphor.
7. Fit the form to the actual slide slot. Do not import a mobile poster ratio into a wide PPT layout without recomposition.
8. Keep titles, labels, captions, numbers, and conclusions as editable PPT text.

## Media Treatment Lock

The template media treatment is authoritative. Before generated-image planning, inspect the selected pack's body, process, compare, data, and cover images and record the closest real assets in `media_treatment_references`. Extract their dimensionality, material, lighting, depth, photography/CGI/illustration method, crop behavior, and subject scale.

Use this order:

1. Use authorized source screenshots or evidence when they carry required facts, framed through the template layout.
2. Use the template's own image assets as treatment references, never as copied content.
3. Use native PPT objects when they communicate the idea more clearly.
4. Only when the needed subject is still missing, use an external visual-intent capability under `visual_intent_only` to decide what to depict and the image form.
5. Render that subject with the template's recorded media treatment. Do not inherit the adapter's hand-drawn, cartoon, photographic, or CGI defaults.

A three-dimensional or cinematic template must yield three-dimensional or cinematic fallback visuals. A hand-drawn fallback is valid only when the confirmed template itself is hand-drawn or the user explicitly overrides the treatment.

## Style Sovereignty

The PPT style lock is authoritative for palette, typography mood, line work, texture, lighting, shape language, image treatment, density, and composition rhythm. Image-form reasoning may change what is depicted and how facts relate; it may not establish a second visual style.

Precedence is:

```text
system/developer/user instructions
> confirmed PPT style lock
> style-pack visual contract
> template media treatment references
> slide layout contract
> image form
> optional character identity
> external generator defaults
```

If a source or generated asset conflicts with the deck, recompose or redraw it under `inherit_ppt_style`. If the character identity cannot survive that transformation, remove the character and preserve the explanatory image form. Never change the deck style to accommodate an image.

## Interaction Gate

- Before confirmation, show only the proposed media count, source policy, generated-visual fallback, and whether an optional character form is recommended.
- Create the final `media-plan.json` only after the user or parent Agent confirms the PPT style.
- A character or IP role is a material choice only when `character_mode` is not `none`. Show a baseline preview already transformed into the PPT style and require explicit confirmation before batch generation.
- Do not ask the user to choose an external skin or painting style. The only visual style choice is the PPT style candidate flow.
- In Agent mode, return unresolved character use to the parent Agent; the capability provider never contacts the end user.

## Conflict Handling

Reject the plan or returned asset when it changes the style authority, omits or mismatches the style-pack media treatment references, places generated visuals before viable source assets, bakes required text into pixels, or uses an unconfirmed character. Retry once with the same PPT style and media-treatment lock. If the adapter cannot comply, fall back to native PPT structure or return `blocked`; do not silently relax the style.
