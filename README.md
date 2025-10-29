# lablab-bean-orchestrator

Control plane for managing spec-driven, multi-repo work using LangChain/LangGraph (or DeepAgents) with per-spec git worktrees and optional containers on a Mac mini host. Triggerable from GitHub (workflow dispatch) or via Windows PowerShell over SSH.

## What This Provides
- Spec lifecycle: activate → create branches → start per-repo environments → open draft PRs (optional)
- Isolation: one git worktree per `{spec_id, repo}`; optional one container per worktree
- Triggers: GitHub Actions (self-hosted runner on the Mac) or Windows → SSH → Mac script
- Config-driven per-repo behavior via `configs/repos.json`

## Prerequisites (Mac mini host)
- git 2.39+
- Docker Desktop, or Colima + Docker CLI (optional if you skip containers)
- jq (for JSON parsing)
- GitHub CLI (`gh`) if you want to auto-open PRs
- A self-hosted GitHub Actions runner on the Mac with labels you control (e.g., `self-hosted,macOS,arm64,spec`)

## Layout
- `scripts/mac/specctl.sh` — main orchestrator (start/stop/status)
- `scripts/py/specctl.py` — Python alternative to `specctl.sh` (cross-platform-friendly)
- `scripts/windows/specctl.ps1` — Windows wrapper that SSH-es into the Mac
- `configs/repos.json` — per-repo settings (image, ports, base branch, etc.)
- `.github/workflows/specctl.yml` — GitHub workflow to trigger `start` from the Actions UI
- `.github/workflows/spec-verify.yml` — GitHub workflow to verify repos can be orchestrated (remotes, branches, containers)
- `Taskfile.yml` — convenience tasks for orchestrator commands
- `templates/**/Taskfile.yml` — task runners for target repos (Unity/.NET/Python)
- `specs/` — local spec registry and documents
- `agents/langgraph/graph.py` — LangGraph controller skeleton (no vendor lock-in)

## Quick Start
1) Edit `configs/repos.json` to match your repos and desired container images.
2) On the Mac mini, set env vars (e.g., in shell profile):
   - `export LABLAB_ORG="your-github-org-or-user"`
   - `export LABLAB_REPOS_BASE="/srv/repos"` (bare clones)
   - `export LABLAB_SPECS_BASE="/srv/specs"` (worktrees)
3) Trigger from GitHub Actions → `Start Spec` workflow, or from Windows:
   - `scripts/windows/specctl.ps1 -SpecId 123 -Slug login -Repos "lablab-bean,lablab-bean-console"`
   - Or use Task on the Mac: `task spec:start SPEC_ID=123 SLUG=login REPOS=lablab-bean,lablab-bean-console`

### Using the Python orchestrator
- Start: `python3 scripts/py/specctl.py start --spec 123 --slug login --repos lablab-bean,lablab-bean-console`
- Status: `python3 scripts/py/specctl.py status --spec 123 --slug login --repos lablab-bean`
- Stop: `python3 scripts/py/specctl.py stop --spec 123 --slug login --repos lablab-bean`
- Bootstrap (re-run template application): `python3 scripts/py/specctl.py bootstrap --spec 123 --slug login --repos lablab-bean,lablab-bean-unity`
- Check (verify before start): `python3 scripts/py/specctl.py check --spec 123 --slug login --repos lablab-bean,lablab-bean-unity`

### Creating and Managing Specs
- Create via GitHub: New Issue → “New Spec”, provide slug, summary, repos. This lives in the orchestrator repo and becomes the source of truth.
- Or import existing docs: `task spec:import SRC=../lablab-bean/docs/_inbox REPOS=lablab-bean`
  - This copies markdown files into `specs/<id>-<slug>/spec.md`, writes `meta.json`, and updates `specs/registry.json`.
  - Then run verify/start with the same `spec_id` and `slug`.
 - Or create directly without an issue: `task spec:new SLUG=login REPOS=lablab-bean,lablab-bean-console` to scaffold `spec.md`, `plan.md`, and `tasks.yaml` using templates.

## Branch & Paths
- Branch name: `spec/{spec_id}-{slug}/{repo}` (example: `spec/123-login/core`)
- Bare clone: `${LABLAB_REPOS_BASE}/{repo}.bare`
- Worktree: `${LABLAB_SPECS_BASE}/{spec_id}/{repo}`

## Notes
- Windows or Unity repos may not build inside Linux containers; set `"container": false` in `configs/repos.json` to skip starting a container but still create the worktree and branch.
- You can keep using AutoGen in each container, or go all-in on LangGraph; this repo doesn’t enforce the inner loop, it just provisions environments.
- We include Taskfiles for each project type (Unity/.NET/Python) to standardize commands like `task lint`, `task test`, and `task precommit:install`. For complex logic, prefer Python scripts over long shell commands.
- Start automatically applies the repo’s templates (based on `type` in `configs/repos.json`) to the new worktree. You can re-run at any time with `task spec:bootstrap`.
- Verify orchestration readiness via the workflow “Verify Spec Orchestration” or locally with `task spec:check`.

## GLM / LangGraph
- This repo ships a minimal LangGraph controller at `agents/langgraph/graph.py`. It does not call any external LLMs by default.
- To use GLM 4.x, configure your provider env vars (see `configs/llm.example.env`) and add a simple `call_llm()` in the graph to invoke your API. Keep calls minimal to control cost.
- You can run LangGraph manually on the Mac host; agents can still be humans (Claude Code/Codex/Copilot) working in the worktree while the graph handles orchestration steps.

### Stage Strategy (Cost-Aware)
- Plan/Tasks: Use local assistants (Claude Code/Codex/Copilot) to edit `specs/<id>-<slug>/plan.md` and `tasks.yaml`. No API cost.
- Implement: Use `agents/langgraph/run_tasks.py` with GLM configured to get concrete step suggestions and code patches per task. Or implement manually and use GLM sparingly.

## Next
- Add a `discord/` bot (optional) that calls the GitHub workflow dispatch with `/spec start` commands.
- Wire draft PR automation by enabling `gh` usage in `specctl.sh`.
