#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from datetime import datetime


def load_registry(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"specs": []}


def next_id(registry: dict) -> int:
    ids = [s.get("id") for s in registry.get("specs", []) if isinstance(s.get("id"), int)]
    return (max(ids) + 1) if ids else 1


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--slug", required=True)
    p.add_argument("--repos", required=True, help="comma-separated repos")
    p.add_argument("--title", default="")
    args = p.parse_args()

    root = Path(__file__).resolve().parents[2]
    specs_dir = root / "specs"
    reg_path = specs_dir / "registry.json"
    reg = load_registry(reg_path)
    sid = next_id(reg)

    folder = specs_dir / f"{sid}-{args.slug}"
    folder.mkdir(parents=True, exist_ok=True)

    # seed files from template
    tpl = specs_dir / "templates" / "_template"
    (folder / "spec.md").write_text((tpl / "spec.md").read_text(encoding="utf-8"), encoding="utf-8")
    (folder / "plan.md").write_text((tpl / "plan.md").read_text(encoding="utf-8"), encoding="utf-8")
    # Use tasks.md to align with Spec-Kit conventions in lablab-bean
    (folder / "tasks.md").write_text((tpl / "tasks.md").read_text(encoding="utf-8"), encoding="utf-8")

    meta = {
      "id": sid,
      "slug": args.slug,
      "title": args.title or args.slug.replace('-', ' ').title(),
      "status": "proposed",
      "repos": [r.strip() for r in args.repos.split(",") if r.strip()],
      "created_at": datetime.utcnow().isoformat() + "Z"
    }
    (folder / "meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    reg["specs"].append({"id": sid, "slug": args.slug, "path": str(folder.relative_to(root)), "status": "proposed"})
    reg_path.write_text(json.dumps(reg, indent=2) + "\n", encoding="utf-8")

    print(f"Created spec {sid}-{args.slug} at {folder}")


if __name__ == "__main__":
    main()
