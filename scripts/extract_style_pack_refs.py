#!/usr/bin/env python3
"""Extract multi-page style-pack screenshots from local PDFs or image folders."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageOps


ROLE_ORDER = ["cover", "section", "body", "process", "compare", "data", "quote", "closing"]
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}


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
            raise SystemExit(f"Invalid role mapping: {item!r}. Use role=page-or-file.")
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


def image_files(source_dir: Path) -> list[Path]:
    files = [p for p in source_dir.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTS]
    return sorted(files, key=lambda p: p.name.lower())


def find_pdftoppm() -> str:
    runtime = Path.home() / ".cache" / "codex-runtimes" / "codex-primary-runtime" / "dependencies"
    candidates = [
        os.environ.get("PDFTOPPM"),
        shutil.which("pdftoppm"),
        runtime / "bin" / "override" / "pdftoppm",
        runtime / "native" / "poppler" / "bin" / "pdftoppm",
        runtime / "native" / "poppler" / "poppler" / "bin" / "pdftoppm",
        "/opt/homebrew/bin/pdftoppm",
        "/usr/local/bin/pdftoppm",
        "/usr/bin/pdftoppm",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    raise SystemExit("pdftoppm not found. Install Poppler or set PDFTOPPM=/path/to/pdftoppm.")


def render_pdf_page(source: Path, page_number: int, out_file: Path, dpi: int) -> None:
    if page_number < 1:
        raise SystemExit(f"PDF page numbers are 1-based, got {page_number}")
    pdftoppm = find_pdftoppm()
    with tempfile.TemporaryDirectory() as tmp:
        prefix = Path(tmp) / "page"
        cmd = [
            pdftoppm,
            "-f",
            str(page_number),
            "-l",
            str(page_number),
            "-singlefile",
            "-png",
            "-r",
            str(dpi),
            str(source),
            str(prefix),
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        rendered = prefix.with_suffix(".png")
        if not rendered.exists():
            raise SystemExit(f"pdftoppm did not create expected output for page {page_number}")
        normalize_image(rendered, out_file)


def resolve_image_selector(source: Path, selector: str) -> Path:
    if source.is_file():
        if source.suffix.lower() not in IMAGE_EXTS:
            raise SystemExit(f"Source file is not an image: {source}")
        if selector not in {"1", source.name}:
            raise SystemExit("For a single image source, selector must be 1 or the image filename.")
        return source

    files = image_files(source)
    if not files:
        raise SystemExit(f"No image files found in {source}")
    if selector.isdigit():
        index = int(selector)
        if index < 1 or index > len(files):
            raise SystemExit(f"Image index {index} out of range 1-{len(files)}")
        return files[index - 1]
    candidate = source / selector
    if candidate.exists() and candidate.is_file():
        return candidate
    matches = [p for p in files if p.name == selector]
    if matches:
        return matches[0]
    raise SystemExit(f"Cannot resolve image selector {selector!r} in {source}")


def normalize_image(source: Path, out_file: Path, max_width: int = 1800) -> None:
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as img:
        img = ImageOps.exif_transpose(img)
        if img.mode not in {"RGB", "RGBA"}:
            img = img.convert("RGB")
        if img.width > max_width:
            ratio = max_width / img.width
            img = img.resize((max_width, max(1, int(img.height * ratio))), Image.Resampling.LANCZOS)
        img.save(out_file, "PNG", optimize=True)


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
    width = thumb_w * min(len(thumbs), 3) + gap * (min(len(thumbs), 3) + 1)
    rows = (len(thumbs) + 2) // 3
    row_heights = []
    for row in range(rows):
        row_heights.append(max(img.height for img in thumbs[row * 3 : row * 3 + 3]))
    height = sum(row_heights) + gap * (rows + 1)
    sheet = Image.new("RGB", (width, height), "#f2f2f2")
    y = gap
    for row in range(rows):
        x = gap
        for img in thumbs[row * 3 : row * 3 + 3]:
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


def build_pack(args: argparse.Namespace) -> dict[str, Any]:
    source = Path(args.source).expanduser().resolve()
    if not source.exists():
        raise SystemExit(f"Source not found: {source}")
    pack_id = slug(args.pack_id)
    roles = parse_roles(args.roles)
    root = skill_root()
    output_root = (root / args.output_root).resolve()
    pack_dir = output_root / pack_id
    pack_dir.mkdir(parents=True, exist_ok=True)

    assets: list[dict[str, Any]] = []
    image_paths: list[Path] = []
    for role, selector in roles:
        out_file = pack_dir / f"{role}-01.png"
        if source.is_file() and source.suffix.lower() == ".pdf":
            if not selector.isdigit():
                raise SystemExit(f"PDF selector for role {role} must be a page number")
            render_pdf_page(source, int(selector), out_file, args.dpi)
        else:
            selected = resolve_image_selector(source, selector)
            normalize_image(selected, out_file, args.max_width)
        stat = out_file.stat()
        image_paths.append(out_file)
        assets.append(
            {
                "role": role,
                "selector": selector,
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
        "status": "ok",
        "created_at": now,
        "source": str(source),
        "source_type": "pdf" if source.suffix.lower() == ".pdf" else "image-folder" if source.is_dir() else "image",
        "usage_policy": "Reference visual style only. Do not copy source content, text, logos, brands, subjects, or page-specific claims.",
        "coverage": [asset["role"] for asset in assets],
        "assets": assets,
        "contact_sheet": rel_to_skill(contact_sheet),
        "notes": args.notes or "",
    }
    write_json(pack_dir / "pack.json", pack)
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
    parser = argparse.ArgumentParser(
        description="Extract style-pack reference screenshots from a local PDF, image file, or image folder.",
    )
    parser.add_argument("--source", required=True, help="Local PDF, image file, or image folder.")
    parser.add_argument("--pack-id", required=True, help="Stable style pack id, e.g. ref-18-muse-editorial.")
    parser.add_argument(
        "--roles",
        required=True,
        help="Comma-separated role mappings, e.g. cover=1,body=3,process=6,closing=10.",
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
    parser.add_argument("--dpi", type=int, default=144, help="PDF render DPI.")
    parser.add_argument("--max-width", type=int, default=1800, help="Maximum output image width.")
    parser.add_argument("--notes", default="", help="Optional pack notes.")
    args = parser.parse_args()

    root = skill_root()
    pack = build_pack(args)
    update_index((root / args.index).resolve(), pack)
    print(f"created style pack: {pack['pack_id']}")
    print(f"pack.json: {root / pack['contact_sheet'].replace('contact-sheet.png', 'pack.json')}")
    print(f"contact sheet: {root / pack['contact_sheet']}")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        sys.stderr.write(exc.stderr.decode("utf-8", errors="ignore"))
        raise SystemExit(exc.returncode) from exc
