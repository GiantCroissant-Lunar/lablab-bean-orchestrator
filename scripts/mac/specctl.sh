#!/usr/bin/env bash
set -euo pipefail

# Orchestrator for spec worktrees and optional containers on a Mac host.
# Requires: git, jq, docker (optional), gh (optional)

usage() {
  cat <<EOF
Usage: $(basename "$0") <start|stop|status> \
  --spec <ID> --slug <slug> --repos <comma-list> [--base <branch>]

Env (override as needed):
  LABLAB_ORG           GitHub org/user (required)
  LABLAB_REPOS_BASE    Base dir for bare clones (default: /srv/repos)
  LABLAB_SPECS_BASE    Base dir for worktrees   (default: /srv/specs)
  LABLAB_GH_SSH        SSH remote prefix (default: git@github.com)
EOF
}

LABLAB_ORG=${LABLAB_ORG:-}
LABLAB_REPOS_BASE=${LABLAB_REPOS_BASE:-/srv/repos}
LABLAB_SPECS_BASE=${LABLAB_SPECS_BASE:-/srv/specs}
LABLAB_GH_SSH=${LABLAB_GH_SSH:-git@github.com}

require() { command -v "$1" >/dev/null 2>&1 || { echo "Missing dependency: $1" >&2; exit 1; }; }

ensure_dirs() { mkdir -p "$LABLAB_REPOS_BASE" "$LABLAB_SPECS_BASE"; }

repo_url() { local repo="$1"; echo "$LABLAB_GH_SSH:${LABLAB_ORG}/${repo}.git"; }

ensure_bare() {
  local repo="$1"; local bare="${LABLAB_REPOS_BASE}/${repo}.bare"
  if [ ! -d "$bare" ]; then
    echo "[repo] cloning bare: $repo -> $bare"
    git clone --bare "$(repo_url "$repo")" "$bare"
  fi
  echo "[repo] fetch origin: $repo"
  git --git-dir="$bare" fetch --all --prune
}

ensure_worktree_branch() {
  local repo="$1"; local spec="$2"; local slug="$3"; local base="$4"
  local bare="${LABLAB_REPOS_BASE}/${repo}.bare"
  local wdir="${LABLAB_SPECS_BASE}/${spec}/${repo}"
  local branch="spec/${spec}-${slug}/${repo}"
  mkdir -p "$wdir"
  if [ ! -d "$wdir/.git" ]; then
    echo "[worktree] add $wdir on $branch from origin/$base"
    git --git-dir="$bare" worktree add -B "$branch" "$wdir" "origin/${base}"
  else
    echo "[worktree] exists $wdir; ensuring branch $branch"
    (cd "$wdir" && git fetch && git checkout "$branch" || git checkout -b "$branch")
    (cd "$wdir" && git pull --rebase)
  fi
}

render_compose() {
  local wdir="$1"; local image="$2"; local project="$3"; shift 3
  local ports=("$@")
  local f="$wdir/docker-compose.yml"
  echo "[compose] writing $f"
  {
    echo "version: '3.8'"
    echo "services:"
    echo "  app:"
    echo "    image: ${image}"
    echo "    container_name: ${project}"
    echo "    working_dir: /workspace"
    echo "    volumes:"
    echo "      - ./:/workspace"
    echo "    command: sleep infinity"
    if [ ${#ports[@]} -gt 0 ]; then
      echo "    ports:"
      for p in "${ports[@]}"; do echo "      - \"$p\""; done
    fi
  } > "$f"
}

compose_up() {
  local wdir="$1"; local project="$2"
  (cd "$wdir" && docker compose -p "$project" up -d)
}

compose_down() {
  local wdir="$1"; local project="$2"
  (cd "$wdir" && docker compose -p "$project" down || true)
}

start_repo() {
  local repo="$1"; local spec="$2"; local slug="$3"; local base="$4"; local cfg="$5"
  ensure_bare "$repo"
  ensure_worktree_branch "$repo" "$spec" "$slug" "$base"
  local wdir="${LABLAB_SPECS_BASE}/${spec}/${repo}"
  local project="spec-${spec}-${repo}"
  local container=$(jq -r --arg r "$repo" '.[$r].container // false' "$cfg")
  # Bootstrap templates based on repo type (unity|dotnet|python)
  local rtype=$(jq -r --arg r "$repo" '.[$r].type // empty' "$cfg")
  if [ -n "$rtype" ] && [ "$rtype" != "null" ]; then
    echo "[bootstrap] applying templates for $repo (type=$rtype)"
    bash "$(dirname "$0")/bootstrap-repo.sh" --type "$rtype" --path "$wdir" || echo "[warn] bootstrap failed for $repo"
  fi
  # Sync spec docs into repo worktree to align with Spec-Kit folder layout
  echo "[sync] copying spec docs to $repo worktree"
  python3 "$(cd "$(dirname "$0")/.." && pwd)/py/sync_spec_to_repo.py" --spec "$spec" --slug "$slug" --repo "$repo" || echo "[warn] sync failed for $repo"
  if [ "$container" = "true" ]; then
    local image=$(jq -r --arg r "$repo" '.[$r].image // empty' "$cfg")
    if [ -z "$image" ] || [ "$image" = "null" ]; then
      echo "[warn] container true but no image for $repo — skipping container"
      return 0
    fi
    mapfile -t ports < <(jq -r --arg r "$repo" '.[$r].ports[]? // empty' "$cfg")
    render_compose "$wdir" "$image" "$project" "${ports[@]}"
    compose_up "$wdir" "$project"
  else
    echo "[info] container disabled for $repo"
  fi
}

stop_repo() {
  local repo="$1"; local spec="$2"
  local wdir="${LABLAB_SPECS_BASE}/${spec}/${repo}"
  local project="spec-${spec}-${repo}"
  if [ -f "$wdir/docker-compose.yml" ]; then
    compose_down "$wdir" "$project"
  fi
  if [ -d "$wdir" ]; then
    echo "[worktree] remove $wdir"
    git -C "$wdir" worktree prune || true
    git worktree remove "$wdir" --force || true
  fi
}

status_repo() {
  local repo="$1"; local spec="$2"
  local wdir="${LABLAB_SPECS_BASE}/${spec}/${repo}"
  local project="spec-${spec}-${repo}"
  echo "--- $repo ---"
  if [ -d "$wdir" ]; then
    (cd "$wdir" && echo "path: $wdir" && git rev-parse --abbrev-ref HEAD)
  else
    echo "worktree: (none)"
  fi
  docker ps --format '{{.Names}}\t{{.Status}}' | grep "$project" || echo "container: (none)"
}

bootstrap_repo() {
  local repo="$1"; local spec="$2"; local cfg="$3"
  local wdir="${LABLAB_SPECS_BASE}/${spec}/${repo}"
  local rtype=$(jq -r --arg r "$repo" '.[$r].type // empty' "$cfg")
  if [ -z "$rtype" ] || [ "$rtype" = "null" ]; then
    echo "[bootstrap] no type configured for $repo; skipping"
    return 0
  fi
  if [ ! -d "$wdir" ]; then
    echo "[bootstrap] worktree not found for $repo at $wdir; did you run start?" >&2
    return 1
  fi
  echo "[bootstrap] $repo -> $rtype at $wdir"
  bash "$(dirname "$0")/bootstrap-repo.sh" --type "$rtype" --path "$wdir"
}

check_repo() {
  local repo="$1"; local base="$2"; local cfg="$3"
  local ok=0
  echo "--- $repo ---"
  # Config present
  local present=$(jq -e --arg r "$repo" '.[$r]' "$cfg" >/dev/null 2>&1; echo $?)
  if [ "$present" -ne 0 ]; then echo "config: MISSING"; return 1; fi
  echo "config: OK"
  # Type sanity
  local rtype=$(jq -r --arg r "$repo" '.[$r].type // empty' "$cfg")
  if [ -z "$rtype" ]; then echo "type: MISSING"; ok=1; else echo "type: $rtype"; fi
  # Remote reachable and base branch exists
  local url="$(repo_url "$repo")"
  if git ls-remote "$url" >/dev/null 2>&1; then
    echo "remote: OK ($url)"
    if git ls-remote --heads "$url" "${base}" | grep -q "refs/heads/${base}"; then
      echo "base_branch: OK (${base})"
    else
      echo "base_branch: NOT FOUND (${base})"; ok=1
    fi
  else
    echo "remote: UNREACHABLE ($url)"; ok=1
  fi
  # Container prerequisites
  local container=$(jq -r --arg r "$repo" '.[$r].container // false' "$cfg")
  if [ "$container" = "true" ]; then
    if command -v docker >/dev/null 2>&1; then
      local image=$(jq -r --arg r "$repo" '.[$r].image // empty' "$cfg")
      if [ -n "$image" ] && [ "$image" != "null" ]; then
        if docker image inspect "$image" >/dev/null 2>&1; then
          echo "image: PRESENT ($image)"
        else
          echo "image: NOT LOCAL ($image) — will pull on start"
        fi
      else
        echo "image: MISSING while container=true"; ok=1
      fi
    else
      echo "docker: NOT INSTALLED while container=true"; ok=1
    fi
  else
    echo "container: disabled"
  fi
  return $ok
}

main() {
  if [ $# -lt 1 ]; then usage; exit 1; fi
  local cmd="$1"; shift
  local spec="" slug="" repos="" base=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --spec) spec="$2"; shift 2 ;;
      --slug) slug="$2"; shift 2 ;;
      --repos) repos="$2"; shift 2 ;;
      --base) base="$2"; shift 2 ;;
      -h|--help) usage; exit 0 ;;
      *) echo "Unknown arg: $1"; usage; exit 1 ;;
    esac
  done

  if [ -z "$LABLAB_ORG" ]; then echo "LABLAB_ORG is required" >&2; exit 1; fi
  if [ -z "$spec" ] || [ -z "$slug" ] || [ -z "$repos" ]; then echo "--spec --slug --repos are required" >&2; exit 1; fi
  base=${base:-$(jq -r '.[] | .base_branch' configs/repos.json | head -n1)}

  require git; require jq
  ensure_dirs

  IFS=',' read -r -a arr <<< "$repos"
  case "$cmd" in
    start)
      for r in "${arr[@]}"; do
        local rtrim=$(echo "$r" | xargs)
        local rbase=$(jq -r --arg rr "$rtrim" '.[$rr].base_branch // "'"$base"'"' configs/repos.json)
        start_repo "$rtrim" "$spec" "$slug" "$rbase" "configs/repos.json"
      done
      ;;
    stop)
      for r in "${arr[@]}"; do stop_repo "$(echo "$r" | xargs)" "$spec"; done
      ;;
    status)
      for r in "${arr[@]}"; do status_repo "$(echo "$r" | xargs)" "$spec"; done
      ;;
    check)
      for r in "${arr[@]}"; do
        local rtrim=$(echo "$r" | xargs)
        local rbase=$(jq -r --arg rr "$rtrim" '.[$rr].base_branch // "'"$base"'"' configs/repos.json)
        check_repo "$rtrim" "$rbase" "configs/repos.json" || true
      done
      ;;
    bootstrap)
      for r in "${arr[@]}"; do bootstrap_repo "$(echo "$r" | xargs)" "$spec" "configs/repos.json"; done
      ;;
    *) echo "Unknown command: $cmd"; usage; exit 1 ;;
  esac
}

main "$@"
