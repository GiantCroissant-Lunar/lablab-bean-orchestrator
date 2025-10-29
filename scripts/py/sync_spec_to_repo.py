#!/usr/bin/env python3
"""
Copy a spec folder from orchestrator specs/<id>-<slug> into a repo worktree as specs/NNN-<slug>/.
Keeps Spec-Kit conventions (spec.md, plan.md, tasks.md, plus any subfolders like contracts/).

Usage:
  python3 scripts/py/sync_spec_to_repo.py --spec 123 --slug login --repo lablab-bean

Assumes worktree is at ${LABLAB_SPECS_BASE}/{spec}/{repo}.
"""
import argparse
import os
import shutil
from pathlib import Path


def copy_tree(src: Path, dst: Path):
    dst.mkdir(parents=True, exist_ok=True)
    for p in src.rglob('*'):
        rel = p.relative_to(src)
        target = dst / rel
        if p.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, target)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--spec', required=True)
    ap.add_argument('--slug', required=True)
    ap.add_argument('--repo', required=True)
    args = ap.parse_args()

    root = Path(__file__).resolve().parents[2]
    spec_src = root / 'specs' / f"{args.spec}-{args.slug}"
    if not spec_src.exists():
        raise SystemExit(f"Spec not found: {spec_src}")

    worktree_base = Path(os.environ.get('LABLAB_SPECS_BASE', '/srv/specs')) / args.spec / args.repo
    if not worktree_base.exists():
        raise SystemExit(f"Worktree not found: {worktree_base}")

    spec_dst = worktree_base / 'specs' / f"{int(args.spec):03d}-{args.slug}"
    copy_tree(spec_src, spec_dst)
    print(f"Synced {spec_src} -> {spec_dst}")


if __name__ == '__main__':
    main()
