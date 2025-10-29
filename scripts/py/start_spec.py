#!/usr/bin/env python3
import os
import sys
import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path
import json
from typing import List

import requests

GITHUB_API = "https://api.github.com"


def headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def run(cmd: List[str], cwd: Path | None = None) -> None:
    print(f"$ {' '.join(cmd)}")
    subprocess.run(cmd, cwd=cwd, check=True)


def pad_id(spec_id: str) -> str:
    try:
        return f"{int(spec_id):03d}"
    except Exception:
        return spec_id


def create_pr(org: str, repo: str, base: str, head: str, title: str, body: str, token: str) -> str:
    url = f"{GITHUB_API}/repos/{org}/{repo}/pulls"
    payload = {
        "title": title,
        "head": head,
        "base": base,
        "body": body,
        "draft": True,
    }
    r = requests.post(url, headers=headers(token), json=payload, timeout=60)
    if r.status_code not in (200, 201):
        raise RuntimeError(f"Create PR failed for {repo}: {r.status_code} {r.text}")
    pr = r.json()
    return pr.get("html_url", "")


def main() -> int:
    parser = argparse.ArgumentParser(description="Start Spec via Python")
    parser.add_argument("--spec-id", required=True)
    parser.add_argument("--slug", required=True)
    parser.add_argument("--repos", required=True, help="Comma-separated repos")
    parser.add_argument("--base", default="main")
    parser.add_argument("--org", default=os.environ.get("LABLAB_ORG"))
    parser.add_argument("--work", default=None, help="Optional working dir (default: temp)")
    args = parser.parse_args()

    token = os.environ.get("LABLAB_GH_PAT") or os.environ.get("GH_TOKEN")
    if not token:
        print("ERROR: LABLAB_GH_PAT environment variable not set", file=sys.stderr)
        return 2
    if not args.org:
        print("ERROR: --org not provided and LABLAB_ORG not set", file=sys.stderr)
        return 2

    repos = [r.strip() for r in args.repos.split(",") if r.strip()]

    # Determine orchestrator root and source spec folder
    script_path = Path(__file__).resolve()
    root = script_path.parents[2]  # repo root

    # Compute padded ID before using it
    id_padded = pad_id(args.spec_id)

    spec_src = root / "specs" / f"{id_padded}-{args.slug}"
    if not spec_src.exists():
        print(f"ERROR: Spec folder not found: {spec_src}", file=sys.stderr)
        return 1

    tiers_json = root / "templates" / "tiers" / "tiers.json"
    tiers_schema = root / "templates" / "tiers" / "tiers.schema.json"

    if args.work:
        work = Path(args.work)
        work.mkdir(parents=True, exist_ok=True)
    else:
        work = Path(tempfile.mkdtemp(prefix="specstart-"))

    print(f"Workdir: {work}")

    failed: List[str] = []
    pr_links: List[str] = []

    for repo in repos:
        try:
            target = work / repo
            if target.exists():
                shutil.rmtree(target)

            # Clone using bearer token in header to avoid printing token
            clone_url = f"git@github.com:{args.org}/{repo}.git"
            run(["git", "clone", "--branch", args.base, "--single-branch", clone_url, str(target)])

            # Create spec branch
            branch = f"spec/{id_padded}-{args.slug}/{repo}"
            run(["git", "checkout", "-b", branch], cwd=target)

            # Copy spec docs
            dst = target / "specs" / f"{id_padded}-{args.slug}"
            dst.parent.mkdir(parents=True, exist_ok=True)
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(spec_src, dst)

            # Seed tiers for app repos
            if repo in {"lablab-bean-console", "lablab-bean-windows", "lablab-bean-unity"}:
                shutil.copy2(tiers_json, target / "tiers.json")
                shutil.copy2(tiers_schema, target / "tiers.schema.json")

            # Commit & push
            run(["git", "add", "."], cwd=target)
            run(["git", "-c", "user.name=automation-bot", "-c", "user.email=automation-bot@example.com",
                 "commit", "-m", f"chore(spec): {args.spec_id}-{args.slug} sync spec docs and config"], cwd=target)
            run(["git", "push", "-u", "origin", branch], cwd=target)

            # Create Draft PR
            pr_url = create_pr(
                args.org,
                repo,
                base=args.base,
                head=branch,
                title=f"[SPEC {args.spec_id}] {args.slug} ({repo})",
                body="Auto-created by orchestrator Python script. This PR syncs spec docs and initial config.",
                token=token,
            )
            pr_links.append(f"{repo}: {pr_url}")

        except subprocess.CalledProcessError as e:
            failed.append(f"{repo}: git error {e}")
        except Exception as e:
            failed.append(f"{repo}: {e}")

    print()
    for link in pr_links:
        print(f"PR: {link}")

    if failed:
        print("\nSome repos failed:")
        for f in failed:
            print(f" - {f}")
        return 1

    print("\nStart Spec completed for all repos")
    return 0


if __name__ == "__main__":
    sys.exit(main())
