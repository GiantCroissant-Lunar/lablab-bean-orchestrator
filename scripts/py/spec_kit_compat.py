#!/usr/bin/env python3
"""
Spec-Kit compatibility shim for offline/local use.
Subcommands:
  create --slug <slug> --repos <comma> [--title <title>]
  add-task --spec <id> --slug <slug> --repo <repo> --title <t> --detail <text> [--stage implement]
  add-plan --spec <id> --slug <slug> --section <title> --text <markdown>
"""
import argparse
import json
from pathlib import Path
import yaml


def load_yaml(path: Path):
    if path.exists():
        return yaml.safe_load(path.read_text(encoding="utf-8")) or []
    return []


def save_yaml(path: Path, data):
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def cmd_create(args):
    from new_spec import main as new_spec_main  # type: ignore

    import sys
    sys.argv = [sys.argv[0], "--slug", args.slug, "--repos", args.repos, "--title", args.title or ""]
    new_spec_main()


def cmd_add_task(args):
    root = Path(__file__).resolve().parents[2]
    spec_dir = root / "specs" / f"{args.spec}-{args.slug}"
    tasks_path = spec_dir / "tasks.yaml"
    tasks = load_yaml(tasks_path)
    next_id = 1
    for t in tasks:
        try:
            n = int(str(t.get("id", "0")).split("-")[-1])
            next_id = max(next_id, n + 1)
        except Exception:
            pass
    tasks.append({
        "id": f"T-{next_id}",
        "title": args.title,
        "repo": args.repo,
        "stage": args.stage,
        "type": "code",
        "detail": args.detail,
    })
    save_yaml(tasks_path, tasks)
    print(f"Added task T-{next_id} to {tasks_path}")


def cmd_add_plan(args):
    root = Path(__file__).resolve().parents[2]
    spec_dir = root / "specs" / f"{args.spec}-{args.slug}"
    plan_path = spec_dir / "plan.md"
    with plan_path.open("a", encoding="utf-8") as f:
        f.write(f"\n\n## {args.section}\n\n{args.text}\n")
    print(f"Appended section to {plan_path}")


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("create")
    s.add_argument("--slug", required=True)
    s.add_argument("--repos", required=True)
    s.add_argument("--title", default="")
    s.set_defaults(fn=cmd_create)

    s = sub.add_parser("add-task")
    s.add_argument("--spec", required=True)
    s.add_argument("--slug", required=True)
    s.add_argument("--repo", required=True)
    s.add_argument("--title", required=True)
    s.add_argument("--detail", required=True)
    s.add_argument("--stage", default="implement")
    s.set_defaults(fn=cmd_add_task)

    s = sub.add_parser("add-plan")
    s.add_argument("--spec", required=True)
    s.add_argument("--slug", required=True)
    s.add_argument("--section", required=True)
    s.add_argument("--text", required=True)
    s.set_defaults(fn=cmd_add_plan)

    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()

