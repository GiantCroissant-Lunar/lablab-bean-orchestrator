# Specs in lablab-bean-orchestrator

Specs live here as folders with metadata and a primary spec document. Create them via GitHub issue template or import from existing repos.

## Structure
- `specs/registry.json` — canonical registry of specs and their status
- `specs/<id>-<slug>/spec.md` — main spec document
- `specs/<id>-<slug>/meta.json` — metadata (repos, owner, labels)

## IDs and Slugs
- IDs are integers (e.g., 123) assigned by importer or manually.
- Slugs are short kebab-case (e.g., `login`).

## Lifecycle
- proposed → in-progress → review → done

## Create a Spec
- GitHub → New Issue → “New Spec” template; then run verify/start in Actions.
- Or import from an existing repo using `scripts/py/import_specs.py` and Task.

