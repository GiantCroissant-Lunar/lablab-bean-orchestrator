# Tasks: tiered-architecture

- [ ] T001 Implement tier ranges and validation
  - Define and load tier ranges from `tiers.json`
  - Validate plugin priorities fall within declared tier ranges (Essential/GameGeneral/GameSpecific; Core vs Plugin)
  - Fail fast with clear error messages including plugin id and offending priority

- [ ] T002 Deterministic loader ordering
  - Ordering: Topological (deps) → Tier order → Priority within tier (lower first) → Stable tie-break by plugin id/name
  - Emit final resolved order with plugin id + priority in logs

- [ ] T003 Schema guardrails and CI
  - Ensure `tiers.schema.json` covers ranges and structure
  - Keep JSON schema validation in main CI (already wired)

- [ ] T004 Unit tests
  - Add tests for: invalid priority out of range; cross-tier deps; tie-break determinism
  - Place tests in `tests/` (Core + Management)

- [ ] T005 Repo-specific paths
  - Confirm placement of `tiers.json` and `tiers.schema.json` at repo root is correct for console/windows
  - If paths differ, document in `plan.md` and update loaders

- [ ] T006 Minimal telemetry/logging
  - Add structured logs at load: total plugins, per-tier counts, final order sample

- [ ] T007 Docs sync
  - Keep `specs/003-tiered-architecture/` in each repo updated from orchestrator
  - Re-run Start Spec to resync when tasks/docs change

<!-- Add, split, or re-sequence tasks as needed. Keep IDs stable. -->
