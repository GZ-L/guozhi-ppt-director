#!/usr/bin/env python3
"""Extract multi-image style packs from ZCOOL work pages.

The script reads the page's Next.js data and uses only
pageProps.data.productImages, avoiding avatars, recommended works, and
navigation imagery.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import shutil
import ssl
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from PIL import Image, ImageOps


ROLE_ORDER = ["cover", "section", "body", "process", "compare", "data", "quote", "closing"]
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0 Safari/537.36"
)


def skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def slug(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9_-]+", "-", value.strip()).strip("-").lower()
    if not value:
        raise SystemExit("--pack-id must contain letters, numbers, hyphens, or underscores")
    return value


def parse_roles(raw: str) -> list[tuple[str, str]]:
    roles: list[tuple[str, str]] = []
    seen: set[str] = set()
    for item in [part.strip() for part in raw.split(",") if part.strip()]:
        if "=" in item:
            role, selector = item.split("=", 1)
        elif ":" in item:
            role, selector = item.split(":", 1)
        else:
            raise SystemExit(f"Invalid role mapping: {item!r}. Use role=product-image-index.")
        role = role.strip().lower()
        selector = selector.strip()
        if role not in ROLE_ORDER:
            raise SystemExit(f"Unsupported role {role!r}. Allowed: {', '.join(ROLE_ORDER)}")
        if role in seen:
            raise SystemExit(f"Duplicate role: {role}")
        if not selector:
            raise SystemExit(f"Missing selector for role: {role}")
        seen.add(role)
        roles.append((role, selector))
    if not roles:
        raise SystemExit("--roles is required")
    return sorted(roles, key=lambda pair: ROLE_ORDER.index(pair[0]))


def rel_to_skill(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(skill_root()))
    except ValueError:
        return str(path.resolve())


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def request_bytes(url: str, timeout: int) -> bytes:
    req = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
            "Referer": "https://www.zcool.com.cn/",
        },
    )
    context = ssl.create_default_context()
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            with urlopen(req, timeout=timeout, context=context) as response:
                return response.read()
        except Exception as exc:  # noqa: BLE001 - surface the final urllib/SSL error with context.
            last_error = exc
            if attempt < 2:
                time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Failed to fetch {url}: {last_error}") from last_error


def read_markup(args: argparse.Namespace) -> str:
    if args.html:
        return Path(args.html).expanduser().read_text(encoding="utf-8", errors="ignore")
    return request_bytes(args.source_url, args.timeout).decode("utf-8", errors="ignore")


def next_data(markup: str) -> dict[str, Any]:
    match = re.search(
        r'<script id=["\']__NEXT_DATA__["\'] type=["\']application/json["\']>(.*?)</script>',
        markup,
        flags=re.DOTALL,
    )
    if not match:
        raise SystemExit("Cannot find __NEXT_DATA__ in the supplied ZCOOL page.")
    try:
        return json.loads(html.unescape(match.group(1)))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Cannot parse __NEXT_DATA__: {exc}") from exc


def page_data(markup: str) -> dict[str, Any]:
    data = next_data(markup)
    page = data.get("props", {}).get("pageProps", {}).get("data", {})
    if not isinstance(page, dict):
        raise SystemExit("Cannot locate pageProps.data in __NEXT_DATA__.")
    return page


def image_url(item: dict[str, Any], field: str) -> str | None:
    fields = {
        "display": ["url", "urlBig", "urlSmall"],
        "big": ["urlBig", "url", "urlSmall"],
        "small": ["urlSmall", "url", "urlBig"],
    }[field]
    for key in fields:
        value = item.get(key)
        if isinstance(value, str) and value.startswith(("http://", "https://")):
            return html.unescape(value)
    return None


def product_images(page: dict[str, Any], image_field: str) -> dict[str, dict[str, Any]]:
    images = page.get("productImages") or []
    if not isinstance(images, list):
        raise SystemExit("pageProps.data.productImages is not a list.")
    out: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(images, 1):
        if not isinstance(item, dict):
            continue
        url = image_url(item, image_field)
        if not url or ".gif" in url.lower():
            continue
        out[str(index)] = {
            "index": str(index),
            "url": url,
            "image_type": item.get("imageType"),
            "image_id": item.get("imageId"),
        }
    return out


def normalize_image(source: Path, out_file: Path, max_width: int) -> None:
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as img:
        img = ImageOps.exif_transpose(img)
        if img.mode not in {"RGB", "RGBA"}:
            img = img.convert("RGB")
        if img.width > max_width:
            ratio = max_width / img.width
            img = img.resize((max_width, max(1, int(img.height * ratio))), Image.Resampling.LANCZOS)
        img.save(out_file, "PNG", optimize=True)


def usable_image(path: Path) -> bool:
    if not path.exists() or path.stat().st_size == 0:
        return False
    try:
        with Image.open(path) as img:
            img.verify()
        return True
    except Exception:
        return False


def create_contact_sheet(images: list[Path], out_file: Path) -> None:
    if not images:
        return
    thumbs: list[Image.Image] = []
    thumb_w = 360
    for image in images:
        with Image.open(image) as img:
            img = ImageOps.exif_transpose(img).convert("RGB")
            ratio = thumb_w / img.width
            img = img.resize((thumb_w, max(1, int(img.height * ratio))), Image.Resampling.LANCZOS)
            thumbs.append(img)
    gap = 18
    cols = min(len(thumbs), 3)
    width = thumb_w * cols + gap * (cols + 1)
    rows = (len(thumbs) + cols - 1) // cols
    row_heights = []
    for row in range(rows):
        row_heights.append(max(img.height for img in thumbs[row * cols : row * cols + cols]))
    height = sum(row_heights) + gap * (rows + 1)
    sheet = Image.new("RGB", (width, height), "#f2f2f2")
    y = gap
    for row in range(rows):
        x = gap
        for img in thumbs[row * cols : row * cols + cols]:
            sheet.paste(img, (x, y))
            x += thumb_w + gap
        y += row_heights[row] + gap
    sheet.save(out_file, "PNG", optimize=True)


def read_json(path: Path, fallback: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Cannot parse JSON: {path}: {exc}") from exc


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def url_suffix(url: str) -> str:
    suffix = Path(urlparse(url).path).suffix.lower()
    if suffix in {".png", ".jpg", ".jpeg", ".webp"}:
        return ".jpg" if suffix == ".jpeg" else suffix
    return ".jpg"


def build_pack(args: argparse.Namespace) -> dict[str, Any]:
    if not args.source_url:
        raise SystemExit("--source-url is required")
    pack_id = slug(args.pack_id)
    roles = parse_roles(args.roles)
    root = skill_root()
    pack_dir = (root / args.output_root / pack_id).resolve()
    pack_dir.mkdir(parents=True, exist_ok=True)

    page = page_data(read_markup(args))
    images = product_images(page, args.image_field)
    if not images:
        raise SystemExit("No usable static productImages found.")

    assets: list[dict[str, Any]] = []
    image_paths: list[Path] = []
    raw_dir = pack_dir / "_raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    for role, selector in roles:
        selected = images.get(selector)
        if not selected:
            available = ", ".join(images.keys())
            raise SystemExit(f"Cannot resolve product image {selector!r}. Available: {available}")
        raw_file = raw_dir / f"{role}-{selector}{url_suffix(selected['url'])}"
        if not usable_image(raw_file):
            if raw_file.exists():
                raw_file.unlink()
            raw_file.write_bytes(request_bytes(selected["url"], args.timeout))
        out_file = pack_dir / f"{role}-01.png"
        normalize_image(raw_file, out_file, args.max_width)
        stat = out_file.stat()
        image_paths.append(out_file)
        assets.append(
            {
                "role": role,
                "selector": selector,
                "source_product_image_index": selected["index"],
                "asset_path": rel_to_skill(out_file),
                "content_type": "image/png",
                "bytes": stat.st_size,
                "sha256": sha256_file(out_file),
            }
        )

    contact_sheet = pack_dir / "contact-sheet.png"
    create_contact_sheet(image_paths, contact_sheet)
    now = datetime.now(timezone.utc).isoformat()
    pack = {
        "pack_id": pack_id,
        "status": args.status,
        "created_at": now,
        "source": args.source_url,
        "source_type": "zcool-work-page",
        "usage_policy": "Reference visual style only. Do not copy source content, text, logos, brands, subjects, or page-specific claims.",
        "coverage": [asset["role"] for asset in assets],
        "assets": assets,
        "contact_sheet": rel_to_skill(contact_sheet),
        "notes": args.notes or "",
    }
    write_json(pack_dir / "pack.json", pack)
    shutil.rmtree(raw_dir, ignore_errors=True)
    return pack


def update_index(index_path: Path, pack: dict[str, Any]) -> None:
    fallback = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "schema": "guozhi-ppt-director-style-pack-index-v1",
        "usage_policy": "Reference visual style only. Do not copy source content, text, logos, brands, subjects, or page-specific claims.",
        "packs": [],
    }
    index = read_json(index_path, fallback)
    packs = [p for p in index.get("packs", []) if isinstance(p, dict) and p.get("pack_id") != pack["pack_id"]]
    packs.append(pack)
    packs.sort(key=lambda item: str(item.get("pack_id", "")))
    index["packs"] = packs
    index["updated_at"] = datetime.now(timezone.utc).isoformat()
    write_json(index_path, index)


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract a style pack from a ZCOOL work page.")
    parser.add_argument("--source-url", required=True, help="ZCOOL work page URL.")
    parser.add_argument("--html", help="Optional cached HTML path for repeatable extraction.")
    parser.add_argument("--pack-id", required=True, help="Stable style pack id, e.g. ref-01-blue-tech.")
    parser.add_argument(
        "--roles",
        required=True,
        help="Comma-separated role mappings using productImages indexes, e.g. cover=1,body=2,data=6.",
    )
    parser.add_argument(
        "--image-field",
        choices=["display", "big", "small"],
        default="display",
        help="Use display width image by default; big can be slower and is rarely needed for style reference.",
    )
    parser.add_argument(
        "--output-root",
        default="assets/style-library/style-packs",
        help="Output root relative to the skill folder.",
    )
    parser.add_argument(
        "--index",
        default="references/style-library/style-pack-index.json",
        help="Style pack index path relative to the skill folder.",
    )
    parser.add_argument("--max-width", type=int, default=1800, help="Maximum output image width.")
    parser.add_argument("--timeout", type=int, default=45, help="Network timeout per request.")
    parser.add_argument("--status", choices=["ok", "limited"], default="ok", help="Pack status.")
    parser.add_argument("--notes", default="", help="Optional pack notes.")
    args = parser.parse_args()

    root = skill_root()
    pack = build_pack(args)
    update_index((root / args.index).resolve(), pack)
    print(f"created style pack: {pack['pack_id']} ({pack['status']})")
    print(f"contact sheet: {root / pack['contact_sheet']}")


if __name__ == "__main__":
    main()
