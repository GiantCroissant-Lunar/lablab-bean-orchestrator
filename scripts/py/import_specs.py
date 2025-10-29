#!/usr/bin/env python3
"""
Import existing spec markdown files into the orchestrator registry.
Usage:
  python3 scripts/py/import_specs.py --src ../lablab-bean/docs/_inbox --default-repos lablab-bean

Creates specs/<id>-<slug>/spec.md and meta.json, updates specs/registry.json.
Assigns IDs sequentially from existing registry.
"""
import argparse
import json
import os
import re
import shutil
from pathlib import Path


def slugify(name: str) -> str:
    s = name.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "spec"


def next_id(registry: dict) -> int:
    ids = [s.get("id") for s in registry.get("specs", []) if isinstance(s.get("id"), int)]
    return (max(ids) + 1) if ids else 1


def load_registry(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"specs": []}


def save_registry(path: Path, reg: dict):
    path.write_text(json.dumps(reg, indent=2) + "\n", encoding="utf-8")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--src", required=True, help="Folder with .md files to import")
    p.add_argument("--default-repos", default="lablab-bean", help="Comma-separated repos for meta")
    p.add_argument("--prefix", default="", help="Optional ID prefix for grouping (ignored in folder name)")
    args = p.parse_args()

    root = Path(__file__).resolve().parents[2]
    specs_dir = root / "specs"
    reg_path = specs_dir / "registry.json"
    reg = load_registry(reg_path)
    cur_id = next_id(reg)

    src = Path(args.src)
    if not src.exists():
        raise SystemExit(f"Source not found: {src}")

    repos = [r.strip() for r in args.default_repos.split(",") if r.strip()]

    for f in sorted(src.glob("*.md")):
        slug = slugify(f.stem)
        sid = cur_id
        cur_id += 1
        folder = specs_dir / f"{sid}-{slug}"
        folder.mkdir(parents=True, exist_ok=True)
        # Copy markdown
        dest_md = folder / "spec.md"
        shutil.copyfile(f, dest_md)
        # Write meta
        meta = {
            "id": sid,
            "slug": slug,
            "status": "proposed",
            "repos": repos,
            "source": str(f.resolve()),
        }
        (folder / "meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
        # Update registry
        reg["specs"].append({"id": sid, "slug": slug, "path": str(folder.relative_to(root)), "status": "proposed"})
        print(f"Imported {f.name} -> {folder}")

    save_registry(reg_path, reg)
    print("Done. Update repos per spec in meta.json as needed.")


if __name__ == "__main__":
    main()
