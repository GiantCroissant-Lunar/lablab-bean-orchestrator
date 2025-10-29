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
    tasks_md = spec_dir / "tasks.md"
    if not tasks_md.exists():
        raise SystemExit(f"No tasks.md found at {tasks_md}")

    tasks_text = tasks_md.read_text(encoding="utf-8")
    # Minimal parse: extract lines like "- [ ] T123 ..." for target repo context later if needed
    # For now, pass the full tasks.md to the LLM for suggestions scoped to the chosen repo.
    # Find worktree on the Mac host convention (/srv/specs/<id>/<repo>)
    worktree = Path(os.getenv("LABLAB_SPECS_BASE", "/srv/specs")) / args.spec / args.repo

    print(f"Spec: {args.spec}-{args.slug}\nRepo: {args.repo}\nWorktree: {worktree}")

    print("\n=== Suggested implementation plan for repo ===")
    messages = [
        {"role": "system", "content": "You are a helpful code assistant. Read tasks.md and propose concrete steps and code patches for ONLY the specified repository."},
        {"role": "user", "content": f"Repository: {args.repo}\nWorktree: {worktree}\n\nTasks.md contents:\n\n{tasks_text}\n\nConstraints:\n- Only modify files under the repository worktree.\n- Prefer minimal diffs and small, verifiable steps.\n- Output proposed unified diffs where applicable."},
    ]
    resp = call_llm(messages)
    print(resp.get("content"))

    print("\nDone. Apply suggested changes manually or extend runner to apply patches automatically.")


if __name__ == "__main__":
    main()
