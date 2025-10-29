#!/usr/bin/env python3
"""
Prototype task runner that reads specs/<id>-<slug>/tasks.yaml and, for each 'implement' task,
invokes the LLM (GLM via OpenAI-compatible) with the task context. This is a safe scaffold:
- It prints suggested steps instead of modifying code.
- You can copy/paste into Claude Code/Codex if preferred.

Later, replace printouts with automated patching bounded to the worktree.
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path

import yaml

from .llm import call_llm


def run_cmd(cmd, cwd=None):
    print(f"$ {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=cwd, check=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--spec", required=True, help="spec id")
    p.add_argument("--slug", required=True)
    p.add_argument("--repo", required=True, help="target repo for tasks")
    args = p.parse_args()

    root = Path(__file__).resolve().parents[2]
    spec_dir = root / "specs" / f"{args.spec}-{args.slug}"

    # Prefer Spec‑Kit tasks.yaml if present; fallback to tasks.md
    tasks_yaml = spec_dir / "tasks.yaml"
    tasks_md = spec_dir / "tasks.md"

    context_blob = ""
    if tasks_yaml.exists():
        try:
            tasks = yaml.safe_load(tasks_yaml.read_text(encoding="utf-8")) or []
        except Exception as e:
            raise SystemExit(f"Failed to parse {tasks_yaml}: {e}")

        # Filter to the selected repo and stage 'implement' by default
        filtered = []
        for t in tasks:
            if not isinstance(t, dict):
                continue
            repo_ok = (t.get("repo") == args.repo) if t.get("repo") else True
            stage = (t.get("stage") or "").lower()
            stage_ok = (stage in ("implement", "build", "code", ""))
            if repo_ok and stage_ok:
                filtered.append(t)

        if not filtered:
            # If nothing matched, fall back to all tasks for visibility
            filtered = [t for t in tasks if isinstance(t, dict)]

        lines = [
            "Tasks (from tasks.yaml, filtered for repo where applicable):",
        ]
        for t in filtered:
            tid = t.get("id", "T-?")
            title = t.get("title", "")
            repo = t.get("repo", "")
            detail = t.get("detail", "")
            stage = t.get("stage", "")
            lines.append(f"- {tid} [{repo}] ({stage}) {title}\n  {detail}")
        context_blob = "\n".join(lines)

    elif tasks_md.exists():
        # Pass through tasks.md for human-authored context
        context_blob = tasks_md.read_text(encoding="utf-8")
    else:
        raise SystemExit(f"No tasks.yaml or tasks.md found in {spec_dir}")
    # Find worktree on the Mac host convention (/srv/specs/<id>/<repo>)
    worktree = Path(os.getenv("LABLAB_SPECS_BASE", "/srv/specs")) / args.spec / args.repo

    print(f"Spec: {args.spec}-{args.slug}\nRepo: {args.repo}\nWorktree: {worktree}")

    print("\n=== Suggested implementation plan for repo ===")
    messages = [
        {"role": "system", "content": "You are a helpful code assistant. Read tasks.md and propose concrete steps and code patches for ONLY the specified repository."},
        {"role": "user", "content": f"Repository: {args.repo}\nWorktree: {worktree}\n\nTasks context (YAML preferred, MD fallback):\n\n{context_blob}\n\nConstraints:\n- Only modify files under the repository worktree.\n- Prefer minimal diffs and small, verifiable steps.\n- Output proposed unified diffs where applicable."},
    ]
    resp = call_llm(messages)
    print(resp.get("content"))

    print("\nDone. Apply suggested changes manually or extend runner to apply patches automatically.")


if __name__ == "__main__":
    main()
