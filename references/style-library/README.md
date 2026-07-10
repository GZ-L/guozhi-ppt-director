# Style Library

This folder stores visual style references for `guozhi-ppt-director`, including public web metadata images, browser screenshots, and user-supplied local PDF/image screenshots. Local PDFs and image folders should become **style packs**, not single cover screenshots.

## Policy

- Use these assets only for visual style analysis.
- Do not copy source page content, text, logos, product claims, people, brands, or specific creative concepts.
- Extract reusable traits only: color mood, layout rhythm, typography hierarchy, spacing, image treatment, texture, chart/interface treatment, and motion direction.
- Prefer public first-image metadata for lightweight web collection, then use browser first-screen screenshots when the page has no metadata image or the user explicitly asks for page screenshots.
- When the user supplies local PDFs or image folders as style references, create a style pack with 4-8 representative screenshots across page roles. Save the pack under `assets/style-library/style-packs/<pack-id>/` and record it in `references/style-library/style-pack-index.json`.
- Treat legacy single screenshots under `assets/style-library/zcool-first-screen/` as `cover-only` unless an associated style pack exists.

## Recommended Collection Method

Run from the Skill folder for lightweight reference images:

```bash
python3 scripts/collect_style_refs.py
```

The script fetches public page HTML, extracts `og:image`, `twitter:image`, or JSON-LD `image`, downloads the image into `assets/style-library/zcool-first-screen/`, and merge-upserts `references/style-library/zcool-style-index.json`. Existing local PDF/image entries are preserved unless their `source_url` matches a newly collected reference.

Run this optional browser screenshot fallback only when a metadata image is missing or the user asks for real first-screen screenshots:

```bash
node scripts/capture_style_screenshots.mjs --only-missing
```

This script requires Playwright plus a local Chrome/Chromium executable. If unavailable, keep the metadata images and record the missing screenshot in the index.

## Style Pack Collection For Local Documents

For PDFs or image folders provided by the user, capture multiple page roles instead of the first page only:

| Role | Use For | Minimum Evidence |
| --- | --- | --- |
| `cover` | opening / hero / title page | required |
| `body` | normal content page | required |
| `process` | workflow / method / step page | required for method-heavy decks |
| `compare` | before-after / contrast / judgment page | recommended |
| `data` | list / chart / dense information page | recommended |
| `section` | chapter divider / transition page | optional |
| `quote` | statement / big idea page | optional |
| `closing` | summary / ending page | required when available |

Recommended pack size: 4-8 screenshots. Do not exceed 10 screenshots unless the style has materially different page systems. If a source has only a cover or theme page, mark the reference as `cover-only` and do not use it as the default primary reference for a full deck.

Use:

```bash
python3 scripts/extract_style_pack_refs.py \
  --source /path/to/reference.pdf \
  --pack-id ref-18-muse-editorial \
  --roles cover=1,body=3,process=6,compare=8,closing=12
```

For image folders, the role value can be a 1-based sorted image index or a filename:

```bash
python3 scripts/extract_style_pack_refs.py \
  --source /path/to/reference-images \
  --pack-id ref-16-black-ai-editorial \
  --roles cover=w1366.png,body=2,process=3,closing=5
```

After extracting a pack, update `zcool-style-catalog.md` with the pack ID, page-role coverage, and continuity notes. Keep `zcool-style-index.json` only for legacy single-image references. Do not store whole source PDFs in the Skill unless the user explicitly asks.

After any style-library mutation, run `python3 scripts/validate_contract.py` before reporting success.

## Style Pack Collection For ZCOOL Work Pages

For ZCOOL work pages that expose `pageProps.data.productImages`, create a multi-image style pack from the work images instead of relying on `og:image` only:

```bash
python3 scripts/extract_zcool_style_pack.py \
  --source-url https://www.zcool.com.cn/work/ZNjg0Nzg1Mjg=.html \
  --pack-id ref-01-premium-blue-tech-keynote \
  --roles cover=1,section=3,body=2,process=6,compare=7,data=9
```

The role selector is the 1-based index in `productImages`. The script ignores GIFs and uses only the work's product images, not recommendations, avatars, author cards, or navigation art. If the page exposes only one usable static image or mostly KV/render assets rather than a page system, set `--status limited` and document that limitation in `zcool-style-catalog.md`.

## Runtime Use

When a user asks for a high-aesthetic PPT or provides a topic:

1. Read `references/style-library/style-match-rules.md`.
2. Read `references/style-library/zcool-style-catalog.md`.
3. Read `references/style-library/zcool-style-index.json` if it exists.
4. Read `references/style-library/style-pack-index.json` when available and prefer packs with role coverage matching the requested deck.
5. Inspect `assets/style-library/zcool-first-screen/contact-sheet.jpg`, the selected single images, or the selected pack images when visual access is available.
6. Match by intent, audience, mood, density, deliverable route, and page-role coverage.
7. Fill `templates/style-match.md`.
8. Use selected references only to write `style-board.md`.
9. Before rendering, use `references/layout-contracting.md` to convert the selected style pack into original layout contracts. The style library supplies visual grammar; it is not a license to copy template assets or external page designs.
