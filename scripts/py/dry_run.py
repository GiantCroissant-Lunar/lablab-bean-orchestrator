#!/usr/bin/env python3
import os
import sys
import json
import argparse
from typing import List, Tuple

import requests

GITHUB_API = "https://api.github.com"


def headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def check_branch(org: str, repo: str, branch: str, token: str) -> Tuple[bool, int]:
    url = f"{GITHUB_API}/repos/{org}/{repo}/branches/{branch}"
    r = requests.get(url, headers=headers(token), timeout=30)
    return r.status_code == 200, r.status_code


def check_push_permission(org: str, repo: str, token: str) -> Tuple[bool, int, str]:
    url = f"{GITHUB_API}/repos/{org}/{repo}"
    r = requests.get(url, headers=headers(token), timeout=30)
    if r.status_code != 200:
        return False, r.status_code, r.text
    data = r.json()
    perms = data.get("permissions") or {}
    return bool(perms.get("push")), r.status_code, ""


def parse_args():
    p = argparse.ArgumentParser(description="Spec Dry Run via Python")
    p.add_argument("--repos", required=True, help="Comma-separated repo list")
    p.add_argument("--base", default="main", help="Base branch")
    p.add_argument("--org", default=os.environ.get("LABLAB_ORG"), help="GitHub org/user")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    token = os.environ.get("LABLAB_GH_PAT") or os.environ.get("GH_TOKEN")
    if not token:
        print("ERROR: LABLAB_GH_PAT environment variable not set", file=sys.stderr)
        return 2
    if not args.org:
        print("ERROR: --org not provided and LABLAB_ORG not set", file=sys.stderr)
        return 2

    repos: List[str] = [r.strip() for r in args.repos.split(",") if r.strip()]
    failures: List[str] = []

    print(f"Org: {args.org}")
    print(f"Base: {args.base}")
    print(f"Repos: {', '.join(repos)}")
    print()

    for repo in repos:
        ok_branch, code_branch = check_branch(args.org, repo, args.base, token)
        ok_push, code_push, err = check_push_permission(args.org, repo, token)
        print(f"[{repo}] branch={ok_branch} (code={code_branch}) push_perm={ok_push} (code={code_push})")
        if not ok_branch:
            failures.append(f"{repo}: missing branch {args.base}")
        if not ok_push:
            failures.append(f"{repo}: token has no push permission")

    print()
    if failures:
        print("Dry-run FAILED:")
        for f in failures:
            print(f" - {f}")
        return 1

    print("Dry-run OK for all repos")
    return 0


if __name__ == "__main__":
    sys.exit(main())
