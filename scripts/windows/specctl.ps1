param(
  [Parameter(Mandatory=$true)][string]$SpecId,
  [Parameter(Mandatory=$true)][string]$Slug,
  [Parameter(Mandatory=$true)][string]$Repos,
  [string]$Base = "main",
  [ValidateSet('start','stop','status')][string]$Command = 'start'
)

# Requires: OpenSSH client on Windows, and SSH access to the Mac host.
# Env vars:
#   $env:LABLAB_MAC_HOST  (e.g., mac-mini.local or 192.168.1.50)
#   $env:LABLAB_MAC_USER  (ssh username)
#   $env:LABLAB_ORCH_DIR  (path to this repo on the Mac, e.g., /Users/you/src/lablab-bean-orchestrator)

if (-not $env:LABLAB_MAC_HOST -or -not $env:LABLAB_MAC_USER -or -not $env:LABLAB_ORCH_DIR) {
  Write-Error "Set LABLAB_MAC_HOST, LABLAB_MAC_USER, LABLAB_ORCH_DIR env vars."
  exit 1
}

$remote = "$($env:LABLAB_MAC_USER)@$($env:LABLAB_MAC_HOST)"
$script = "cd '$($env:LABLAB_ORCH_DIR)' && bash scripts/mac/specctl.sh $Command --spec '$SpecId' --slug '$Slug' --repos '$Repos' --base '$Base'"

Write-Host "[ssh] $remote => $script"
ssh $remote $script
