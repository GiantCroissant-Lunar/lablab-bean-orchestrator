# Spec 003: Tiered Architecture — Apply Guide

This repo hosts Spec‑Kit docs and automation. Tasks are defined in `specs/003-tiered-architecture/tasks.yaml` (canonical), with `tasks.md` for readability.

Workflows:
- Spec Run Tasks (GLM optional): suggest steps/diffs (no writes).
- Spec Apply Tasks (auto-apply): apply to a single repo/branch with optional `task_id`.
- Spec Apply (simple): input only `spec_id`; discovers repos/branches from tasks.yaml and pushes changes when build/test pass.

Quickstart
1) Suggest (safe):
   - Actions → Spec Run Tasks → spec_id=003, slug=tiered-architecture, repo=lablab-bean-console
2) Apply (simple, spec_id only):
   - Actions → Spec Apply (simple)
   - spec_id=003 (optional repos filter: `lablab-bean-console`)
3) Apply (targeted):
   - Actions → Spec Apply Tasks (auto-apply)
   - spec_id=003, slug=tiered-architecture, repo=lablab-bean-console, branch=spec/003-tiered-architecture/lablab-bean-console-gh, task_id=T-1 (optional)

Notes
- Pushing requires `secrets.LABLAB_GH_PAT` with Contents & Pull Requests write on target repos.
- CI validates tiers.json against tiers.schema.json in app repos.
