#!/usr/bin/env python3
import argparse
import json
import os
from pathlib import Path
from typing import Dict, List, Optional

import requests
import yaml

GITHUB_API = "https://api.github.com"


def pad_id(spec_id: str) -> str:
    try:
        return f"{int(spec_id):03d}"
    except Exception:
        return spec_id


def headers(token: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def branch_exists(org: str, repo: str, branch: str, token: str) -> bool:
    url = f"{GITHUB_API}/repos/{org}/{repo}/branches/{branch}"
    r = requests.get(url, headers=headers(token), timeout=30)
    return r.status_code == 200


def main() -> int:
    p = argparse.ArgumentParser(description="Resolve apply matrix from spec")
    p.add_argument("--spec-id", required=True)
    p.add_argument("--org", required=True)
    p.add_argument("--repos", default=None, help="Optional comma-separated filter list")
    args = p.parse_args()

    token = os.environ.get("LABLAB_GH_PAT") or os.environ.get("GH_TOKEN")
    if not token:
        raise SystemExit("LABLAB_GH_PAT not set")

    root = Path(__file__).resolve().parents[2]
    # Find slug from registry
    reg = json.loads((root / "specs" / "registry.json").read_text(encoding="utf-8"))
    slug: Optional[str] = None
    in_str = str(args.spec_id)
    in_norm = str(int(args.spec_id)) if str(args.spec_id).isdigit() else in_str
    for s in reg.get("specs", []):
        sid = s.get("id")
        sid_str = str(sid)
        if sid_str == in_str or sid_str == in_norm:
            slug = s.get("slug")
            break
    if not slug:
        raise SystemExit("Spec not found in registry")

    spec_id_p = pad_id(args.spec_id)
    spec_dir = root / "specs" / f"{spec_id_p}-{slug}"
    tasks_yaml = spec_dir / "tasks.yaml"
    repos: List[str] = []
    if tasks_yaml.exists():
        data = yaml.safe_load(tasks_yaml.read_text(encoding="utf-8")) or []
        for t in data:
            if isinstance(t, dict) and t.get("repo"):
                repos.append(t["repo"])
    # fallback to meta.json repos
    if not repos and (spec_dir / "meta.json").exists():
        meta = json.loads((spec_dir / "meta.json").read_text(encoding="utf-8"))
        repos = [r for r in meta.get("repos", []) if r]

    repos = sorted(set(repos))
    if args.repos:
        filt = {r.strip() for r in args.repos.split(",") if r.strip()}
        repos = [r for r in repos if r in filt]

    include = []
    for r in repos:
        candidates = [
            f"spec/{spec_id_p}-{slug}/{r}-gh",
            f"spec/{spec_id_p}-{slug}/{r}",
        ]
        chosen: Optional[str] = None
        for br in candidates:
            if branch_exists(args.org, r, br, token):
                chosen = br
                break
        if chosen:
            include.append({
                "repo": r,
                "branch": chosen,
                "slug": slug,
                "spec": spec_id_p,
            })

    print(json.dumps({"include": include}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
