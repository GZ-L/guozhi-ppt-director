#!/usr/bin/env python3
"""Check whether an external DashiAI PPT Skill/project is available."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path


def candidate_roots() -> list[Path]:
    roots: list[Path] = []
    env = os.environ.get("DASHIAI_PPT_SKILL_ROOT")
    if env:
        roots.append(Path(env).expanduser())

    homes: list[Path] = []
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        homes.append(Path(codex_home).expanduser() / "skills")
    homes.extend([
        Path.home() / ".codex" / "skills",
        Path.home() / ".agents" / "skills",
    ])
    names = ["dashiai-ppt", "dashiAI-ppt", "dashiai-ppt-skill"]
    for base in homes:
        for name in names:
            roots.append(base / name)

    unique: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        key = str(root).casefold()
        if key not in seen:
            unique.append(root)
            seen.add(key)
    return unique


def inspect_root(root: Path) -> dict[str, object]:
    skill = root / "SKILL.md"
    project = root / "project"
    package_json = project / "package.json"
    layout_manifest = project / "layout-manifest.json"
    scripts = project / "scripts"
    theme_grid = root / "assets" / "skill" / "theme-style-grid.png"
    node_modules = project / "node_modules"
    package_version = None
    if package_json.exists():
        try:
            package_version = json.loads(package_json.read_text(encoding="utf-8")).get("version")
        except (json.JSONDecodeError, OSError):
            package_version = None
    node = shutil.which("node")
    chrome_candidates = [
        os.environ.get("CHROME_PATH"),
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        shutil.which("google-chrome"),
        shutil.which("chromium"),
    ]
    chrome = next((item for item in chrome_candidates if item and Path(item).exists()), None)
    usable = skill.exists() and package_json.exists() and layout_manifest.exists() and scripts.exists()
    return {
        "root": str(root),
        "exists": root.exists(),
        "skill_md": skill.exists(),
        "project": project.exists(),
        "package_json": package_json.exists(),
        "layout_manifest": layout_manifest.exists(),
        "scripts": scripts.exists(),
        "theme_grid": str(theme_grid) if theme_grid.exists() else None,
        "node_modules": node_modules.exists(),
        "package_version": package_version,
        "node_executable": node,
        "chrome_executable": chrome,
        "usable": usable,
        "runtime_ready": usable and node is not None,
    }


def main() -> None:
    checked = [inspect_root(root) for root in candidate_roots()]
    usable = next((item for item in checked if item["usable"]), None)
    result = {
        "adapter": "dashiai-ppt",
        "installed": usable is not None,
        "skill_root": usable["root"] if usable else None,
        "project_root": str(Path(str(usable["root"])) / "project") if usable else None,
        "theme_grid": usable["theme_grid"] if usable else None,
        "node_modules": usable["node_modules"] if usable else None,
        "license": "External DashiAI project is AGPL-3.0; keep as user-approved dependency, not vendored Guozhi assets.",
        "runtime_note": "If node_modules is false, DashiAI's first render may install project dependencies before rendering.",
        "install_hint": "Install the external dashiai-ppt dependency only after route dashiai is explicitly confirmed.",
        "checked": checked,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
