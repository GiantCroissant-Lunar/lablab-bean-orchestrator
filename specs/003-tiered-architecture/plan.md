# Plan: Tiered Architecture (Spec 003)

- Context
  - Multi-tier plugin system (Essential → GameGeneral → GameSpecific)
  - Core vs Plugin ranges with explicit priorities per plugin

- Milestones
  - M1: Schema + validation wired (tiers.json + schema; CI check)
  - M2: Loader ordering rules implemented + logs
  - M3: Tests for ranges, ordering determinism, and errors
  - M4: Repo-docs synced and usage notes per app

- Notes
  - Place `tiers.json` and `tiers.schema.json` at repo root (console/windows). Document deviations.
  - Ordering: topo on deps → tier order → in-tier priority (asc) → name tie-break.


## Agent Execution

Use Spec Run Tasks to propose staged diffs per repo. Keep PRs in Draft until all tests pass and schema validation is green.
