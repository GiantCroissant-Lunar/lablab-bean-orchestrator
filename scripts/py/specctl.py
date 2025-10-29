#!/usr/bin/env python3
"""
Python alternative to scripts/mac/specctl.sh for starting/stopping/status of specs.
Uses env vars: LABLAB_ORG, LABLAB_REPOS_BASE, LABLAB_SPECS_BASE
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def sh(cmd, cwd=None, check=True):
    print(f"$ {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=cwd, check=check)


def out(cmd, cwd=None):
    return subprocess.check_output(cmd, cwd=cwd).decode("utf-8", "ignore").strip()


def ensure_dirs(base_repos: Path, base_specs: Path):
    base_repos.mkdir(parents=True, exist_ok=True)
    base_specs.mkdir(parents=True, exist_ok=True)


def repo_url(org: str, repo: str) -> str:
    return f"git@github.com:{org}/{repo}.git"


def ensure_bare(org: str, repo: str, base_repos: Path):
    bare = base_repos / f"{repo}.bare"
    if not bare.exists():
        sh(["git", "clone", "--bare", repo_url(org, repo), str(bare)])
    sh(["git", "--git-dir", str(bare), "fetch", "--all", "--prune"])
    return bare


def ensure_worktree_branch(bare: Path, specs_base: Path, repo: str, spec_id: str, slug: str, base_branch: str):
    wdir = specs_base / spec_id / repo
    branch = f"spec/{spec_id}-{slug}/{repo}"
    wdir.mkdir(parents=True, exist_ok=True)
    git_dir = ["git", "--git-dir", str(bare)]
    if not (wdir / ".git").exists():
        sh(git_dir + ["worktree", "add", "-B", branch, str(wdir), f"origin/{base_branch}"])
    else:
        sh(["git", "fetch"], cwd=wdir)
        # try checkout existing, else create
        try:
            sh(["git", "checkout", branch], cwd=wdir)
        except subprocess.CalledProcessError:
            sh(["git", "checkout", "-b", branch], cwd=wdir)
        sh(["git", "pull", "--rebase"], cwd=wdir)
    return wdir, branch


def render_compose(wdir: Path, image: str, project: str, ports: list[str]):
    compose = wdir / "docker-compose.yml"
    lines = [
        "version: '3.8'",
        "services:",
        "  app:",
        f"    image: {image}",
        f"    container_name: {project}",
        "    working_dir: /workspace",
        "    volumes:",
        "      - ./:/workspace",
        "    command: sleep infinity",
    ]
    if ports:
        lines.append("    ports:")
        for p in ports:
            lines.append(f"      - \"{p}\"")
    compose.write_text("\n".join(lines) + "\n", encoding="utf-8")


def docker_compose_up(wdir: Path, project: str):
    sh(["docker", "compose", "-p", project, "up", "-d"], cwd=wdir)


def docker_compose_down(wdir: Path, project: str):
    try:
        sh(["docker", "compose", "-p", project, "down"], cwd=wdir)
    except Exception:
        pass


def cmd_start(args):
    org = os.environ.get("LABLAB_ORG")
    if not org:
        print("LABLAB_ORG is required")
        sys.exit(1)
    repos_cfg = json.loads(Path("configs/repos.json").read_text(encoding="utf-8"))
    base_repos = Path(os.environ.get("LABLAB_REPOS_BASE", "/srv/repos"))
    base_specs = Path(os.environ.get("LABLAB_SPECS_BASE", "/srv/specs"))
    ensure_dirs(base_repos, base_specs)

    repos = [r.strip() for r in args.repos.split(",") if r.strip()]
    for repo in repos:
        cfg = repos_cfg.get(repo, {})
        base_branch = cfg.get("base_branch") or args.base
        bare = ensure_bare(org, repo, base_repos)
        wdir, _ = ensure_worktree_branch(bare, base_specs, repo, args.spec, args.slug, base_branch)
        # Bootstrap templates based on repo type
        rtype = cfg.get("type")
        if rtype:
            root = Path(__file__).resolve().parents[2]  # repo root
            bootstrap = root / "scripts" / "mac" / "bootstrap-repo.sh"
            if bootstrap.exists():
                print(f"[bootstrap] applying templates for {repo} (type={rtype})")
                sh(["bash", str(bootstrap), "--type", rtype, "--path", str(wdir)])
            else:
                print("[warn] bootstrap script not found; skipping")
        # Sync spec docs into repo worktree to align with Spec-Kit
        sync = Path(__file__).resolve().parents[0] / "sync_spec_to_repo.py"
        if sync.exists():
            print(f"[sync] copying spec docs to {repo} worktree")
            sh(["python3", str(sync), "--spec", args.spec, "--slug", args.slug, "--repo", repo])
        else:
            print("[warn] sync_spec_to_repo.py not found; skipping")
        if cfg.get("container"):
            image = cfg.get("image")
            if image:
                project = f"spec-{args.spec}-{repo}"
                ports = cfg.get("ports", [])
                render_compose(wdir, image, project, ports)
                docker_compose_up(wdir, project)
            else:
                print(f"[warn] container true but no image for {repo}")
        else:
            print(f"[info] container disabled for {repo}")


def cmd_stop(args):
    base_specs = Path(os.environ.get("LABLAB_SPECS_BASE", "/srv/specs"))
    repos = [r.strip() for r in args.repos.split(",") if r.strip()]
    for repo in repos:
        wdir = base_specs / args.spec / repo
        project = f"spec-{args.spec}-{repo}"
        if wdir.exists():
            docker_compose_down(wdir, project)
            # remove worktree
            try:
                sh(["git", "worktree", "remove", str(wdir), "--force"])
            except Exception:
                pass


def cmd_status(args):
    base_specs = Path(os.environ.get("LABLAB_SPECS_BASE", "/srv/specs"))
    repos = [r.strip() for r in args.repos.split(",") if r.strip()]
    for repo in repos:
        wdir = base_specs / args.spec / repo
        print(f"--- {repo} ---")
        if wdir.exists():
            try:
                branch = out(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=wdir)
                print(f"path: {wdir}\nbranch: {branch}")
            except Exception:
                print(f"path: {wdir}")
        else:
            print("worktree: (none)")


def cmd_bootstrap(args):
    base_specs = Path(os.environ.get("LABLAB_SPECS_BASE", "/srv/specs"))
    repos_cfg = json.loads(Path("configs/repos.json").read_text(encoding="utf-8"))
    root = Path(__file__).resolve().parents[2]
    bootstrap = root / "scripts" / "mac" / "bootstrap-repo.sh"
    repos = [r.strip() for r in args.repos.split(",") if r.strip()]
    for repo in repos:
        rtype = repos_cfg.get(repo, {}).get("type")
        if not rtype:
            print(f"[bootstrap] no type configured for {repo}; skipping")
            continue
        wdir = base_specs / args.spec / repo
        if not wdir.exists():
            print(f"[bootstrap] worktree not found for {repo} at {wdir}; run start first")
            continue
        if not bootstrap.exists():
            print("[warn] bootstrap script not found; skipping")
            continue
        print(f"[bootstrap] {repo} -> {rtype} at {wdir}")
        sh(["bash", str(bootstrap), "--type", rtype, "--path", str(wdir)])


def cmd_check(args):
    org = os.environ.get("LABLAB_ORG")
    if not org:
        print("LABLAB_ORG is required")
        sys.exit(1)
    repos_cfg = json.loads(Path("configs/repos.json").read_text(encoding="utf-8"))
    repos = [r.strip() for r in args.repos.split(",") if r.strip()]
    for repo in repos:
        print(f"--- {repo} ---")
        cfg = repos_cfg.get(repo)
        if not cfg:
            print("config: MISSING")
            continue
        print("config: OK")
        rtype = cfg.get("type") or ""
        if not rtype:
            print("type: MISSING")
        else:
            print(f"type: {rtype}")
        url = repo_url(org, repo)
        try:
            out(["git", "ls-remote", url])
            print(f"remote: OK ({url})")
            base = cfg.get("base_branch") or args.base
            try:
                heads = out(["git", "ls-remote", "--heads", url, base])
                if f"refs/heads/{base}" in heads:
                    print(f"base_branch: OK ({base})")
                else:
                    print(f"base_branch: NOT FOUND ({base})")
            except subprocess.CalledProcessError:
                print(f"base_branch: NOT FOUND ({base})")
        except subprocess.CalledProcessError:
            print(f"remote: UNREACHABLE ({url})")
        if cfg.get("container"):
            image = cfg.get("image")
            if not image:
                print("image: MISSING while container=true")
            else:
                try:
                    sh(["docker", "image", "inspect", image], check=True)
                    print(f"image: PRESENT ({image})")
                except Exception:
                    print(f"image: NOT LOCAL ({image}) — will pull on start")


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--spec", required=True)
    common.add_argument("--slug", required=True)
    common.add_argument("--repos", required=True, help="comma-separated")
    common.add_argument("--base", default="main")

    s = sub.add_parser("start", parents=[common])
    s.set_defaults(fn=cmd_start)
    s = sub.add_parser("stop", parents=[common])
    s.set_defaults(fn=cmd_stop)
    s = sub.add_parser("status", parents=[common])
    s.set_defaults(fn=cmd_status)
    s = sub.add_parser("bootstrap", parents=[common])
    s.set_defaults(fn=cmd_bootstrap)
    s = sub.add_parser("check", parents=[common])
    s.set_defaults(fn=cmd_check)

    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
