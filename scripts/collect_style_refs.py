#!/usr/bin/env python3
"""Collect lightweight visual style references from public page metadata.

This script avoids opening pages in a browser. It fetches HTML, extracts
OpenGraph/Twitter/JSON-LD image URLs, downloads those images, and writes a
metadata index for the guozhi-ppt-director style library.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import ssl
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


DEFAULT_URLS = [
    "https://www.zcool.com.cn/work/ZNjg0Nzg1Mjg=.html",
    "https://www.zcool.com.cn/work/ZNzMyNzU2ODA=.html",
    "https://www.zcool.com.cn/work/ZNjgxMTI2MTI=.html",
    "https://www.zcool.com.cn/work/ZNjUxNzEyODQ=.html",
    "https://www.zcool.com.cn/work/ZNjkwMzExMjQ=.html",
    "https://www.zcool.com.cn/work/ZNzAyNzEwMjg=.html",
    "https://www.zcool.com.cn/work/ZNzI3NDM0OTI=.html",
    "https://www.zcool.com.cn/work/ZNzM4MzA1ODQ=.html",
    "https://www.zcool.com.cn/work/ZNzAyNzEwMjg=.html",
    "https://www.zcool.com.cn/events/yipai",
    "https://www.zcool.com.cn/work/ZNzM4MzgxODg=.html",
    "https://www.zcool.com.cn/work/ZNTU0Njg0ODA=.html",
    "https://www.zcool.com.cn/work/ZNjcyOTc4Mjg=.html",
    "https://www.zcool.com.cn/work/ZNzIwMTg2Mjg=.html",
    "https://www.zcool.com.cn/work/ZNDExMzU1NzI=.html",
    "https://www.zcool.com.cn/work/ZNjc1OTczNDA=.html",
]


USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0 Safari/537.36"
)


@dataclass
class RefResult:
    index: str
    source_url: str
    status: str
    page_title: str | None = None
    image_url: str | None = None
    asset_path: str | None = None
    content_type: str | None = None
    bytes: int | None = None
    sha256: str | None = None
    error: str | None = None


def fetch(url: str, timeout: int) -> tuple[bytes, str | None]:
    req = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
            "Referer": "https://www.zcool.com.cn/",
        },
    )
    # Some local Python installs do not have the platform CA chain configured.
    context = ssl.create_default_context()
    with urlopen(req, timeout=timeout, context=context) as response:
        return response.read(), response.headers.get("content-type")


def unique_ordered(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            out.append(value)
    return out


def meta_content(markup: str, key: str) -> str | None:
    patterns = [
        rf'<meta[^>]+property=["\']{re.escape(key)}["\'][^>]+content=["\']([^"\']+)["\']',
        rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']{re.escape(key)}["\']',
        rf'<meta[^>]+name=["\']{re.escape(key)}["\'][^>]+content=["\']([^"\']+)["\']',
        rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']{re.escape(key)}["\']',
    ]
    for pattern in patterns:
        match = re.search(pattern, markup, flags=re.IGNORECASE | re.DOTALL)
        if match:
            return html.unescape(match.group(1))
    return None


def title(markup: str) -> str | None:
    match = re.search(r"<title>(.*?)</title>", markup, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return None
    return re.sub(r"\s+", " ", html.unescape(match.group(1))).strip()


def json_ld_images(markup: str) -> list[str]:
    out: list[str] = []
    for match in re.finditer(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        markup,
        flags=re.IGNORECASE | re.DOTALL,
    ):
        raw = html.unescape(match.group(1)).strip()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        stack = [data]
        while stack:
            item = stack.pop()
            if isinstance(item, dict):
                image = item.get("image")
                if isinstance(image, str):
                    out.append(image)
                elif isinstance(image, list):
                    out.extend([v for v in image if isinstance(v, str)])
                stack.extend(item.values())
            elif isinstance(item, list):
                stack.extend(item)
    return out


def extract_image_url(markup: str) -> str | None:
    candidates = [
        meta_content(markup, "og:image"),
        meta_content(markup, "twitter:image"),
        *json_ld_images(markup),
    ]
    for candidate in candidates:
        if candidate and candidate.startswith(("http://", "https://")):
            return candidate
    return None


def extension_from(content_type: str | None, image_url: str) -> str:
    ctype = (content_type or "").lower()
    if "png" in ctype:
        return ".png"
    if "webp" in ctype:
        return ".webp"
    if "jpeg" in ctype or "jpg" in ctype:
        return ".jpg"
    suffix = Path(urlparse(image_url).path).suffix.lower()
    if suffix in {".png", ".webp", ".jpg", ".jpeg", ".gif"}:
        return ".jpg" if suffix == ".jpeg" else suffix
    return ".jpg"


def collect(
    urls: list[str],
    output_dir: Path,
    timeout: int,
    index_by_url: dict[str, str] | None = None,
    start_index: int = 1,
) -> list[RefResult]:
    output_dir.mkdir(parents=True, exist_ok=True)
    results: list[RefResult] = []
    next_index = start_index
    index_by_url = index_by_url or {}
    for url in unique_ordered(urls):
        if url in index_by_url:
            index = index_by_url[url]
        else:
            index = f"{next_index:02d}"
            next_index += 1
        try:
            page_bytes, _ = fetch(url, timeout)
            markup = page_bytes.decode("utf-8", errors="ignore")
            page_title = title(markup)
            image_url = extract_image_url(markup)
            if not image_url:
                results.append(
                    RefResult(index=index, source_url=url, status="no_image", page_title=page_title)
                )
                continue
            image_bytes, content_type = fetch(image_url, timeout)
            digest = hashlib.sha256(image_bytes).hexdigest()
            ext = extension_from(content_type, image_url)
            asset_name = f"zcool-ref-{index}{ext}"
            asset_file = output_dir / asset_name
            asset_file.write_bytes(image_bytes)
            results.append(
                RefResult(
                    index=index,
                    source_url=url,
                    status="ok",
                    page_title=page_title,
                    image_url=image_url,
                    asset_path=f"assets/style-library/zcool-first-screen/{asset_name}",
                    content_type=content_type,
                    bytes=len(image_bytes),
                    sha256=digest,
                )
            )
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            results.append(RefResult(index=index, source_url=url, status="failed", error=str(exc)))
    return results


def read_existing_index(index_file: Path) -> dict[str, Any]:
    if not index_file.exists():
        return {}
    try:
        return json.loads(index_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Cannot parse existing index: {index_file}: {exc}") from exc


def existing_index_by_url(existing_index: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    for result in existing_index.get("results", []):
        source_url = result.get("source_url")
        index = result.get("index")
        if isinstance(source_url, str) and isinstance(index, str):
            out[source_url] = index
    return out


def next_available_index(existing_index: dict[str, Any]) -> int:
    highest = 0
    for result in existing_index.get("results", []):
        try:
            highest = max(highest, int(str(result.get("index", "0"))))
        except ValueError:
            continue
    return highest + 1


def sort_key(result: dict[str, Any]) -> tuple[int, str]:
    try:
        return (int(str(result.get("index", "0"))), str(result.get("index", "")))
    except ValueError:
        return (9999, str(result.get("index", "")))


def merge_index(existing_index: dict[str, Any], results: list[RefResult], urls: list[str]) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    merged_results: list[dict[str, Any]] = [
        dict(result) for result in existing_index.get("results", []) if isinstance(result, dict)
    ]
    position_by_source = {
        result.get("source_url"): pos
        for pos, result in enumerate(merged_results)
        if isinstance(result.get("source_url"), str)
    }

    for result in results:
        item = result.__dict__
        source_url = item.get("source_url")
        if source_url in position_by_source:
            merged_results[position_by_source[source_url]] = item
        else:
            position_by_source[source_url] = len(merged_results)
            merged_results.append(item)

    merged_results.sort(key=sort_key)
    return {
        **existing_index,
        "created_at": existing_index.get("created_at", now),
        "updated_at": now,
        "method": "metadata_image_extract_no_browser_merge",
        "usage_policy": "Reference visual style only. Do not copy source content, text, logos, brands, subjects, or page-specific claims.",
        "input_count": len(merged_results),
        "unique_count": len(merged_results),
        "duplicate_count": len(urls) - len(unique_ordered(urls)),
        "results": merged_results,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="assets/style-library/zcool-first-screen")
    parser.add_argument("--index", default="references/style-library/zcool-style-index.json")
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--url", action="append", dest="urls")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    output_dir = (root / args.output_dir).resolve()
    index_file = (root / args.index).resolve()
    urls = args.urls or DEFAULT_URLS
    existing_index = read_existing_index(index_file)
    results = collect(
        urls,
        output_dir,
        args.timeout,
        index_by_url=existing_index_by_url(existing_index),
        start_index=next_available_index(existing_index),
    )
    merged_index = merge_index(existing_index, results, urls)
    index_file.parent.mkdir(parents=True, exist_ok=True)
    index_file.write_text(
        json.dumps(merged_index, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    ok = sum(1 for result in results if result.status == "ok")
    print(f"collected={ok}/{len(results)} merged_total={len(merged_index['results'])} index={index_file}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
