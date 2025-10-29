param(
  [Parameter(Mandatory=$true)][ValidateSet('unity','dotnet','python')][string]$Type,
  [Parameter(Mandatory=$true)][string]$Path
)

$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

function Copy-IfExists($src, $dst) {
  if (Test-Path $src) { Copy-Item $src $dst -Force }
}

switch ($Type) {
  'unity' {
    New-Item -ItemType Directory -Force -Path (Join-Path $Path 'scripts/precommit/unity') | Out-Null
    New-Item -ItemType Directory -Force -Path (Join-Path $Path 'scripts/precommit/common') | Out-Null
    Copy-Item (Join-Path $root 'templates/unity/.pre-commit-config.yaml') (Join-Path $Path '.pre-commit-config.yaml') -Force
    Copy-Item (Join-Path $root 'templates/unity/.gitignore') (Join-Path $Path '.gitignore') -Force
    Copy-Item (Join-Path $root 'templates/unity/Taskfile.yml') (Join-Path $Path 'Taskfile.yml') -Force
    Copy-Item (Join-Path $root 'templates/unity/scripts/precommit/unity/check_meta_pairs.py') (Join-Path $Path 'scripts/precommit/unity/check_meta_pairs.py') -Force
    Copy-Item (Join-Path $root 'templates/unity/scripts/precommit/unity/check_editor_settings.py') (Join-Path $Path 'scripts/precommit/unity/check_editor_settings.py') -Force
    Copy-Item (Join-Path $root 'templates/unity/scripts/precommit/common/check_lfs.py') (Join-Path $Path 'scripts/precommit/common/check_lfs.py') -Force
  }
  'dotnet' {
    Copy-Item (Join-Path $root 'templates/dotnet/.pre-commit-config.yaml') (Join-Path $Path '.pre-commit-config.yaml') -Force
    Copy-Item (Join-Path $root 'templates/dotnet/Taskfile.yml') (Join-Path $Path 'Taskfile.yml') -Force
  }
  'python' {
    Copy-Item (Join-Path $root 'templates/python/.pre-commit-config.yaml') (Join-Path $Path '.pre-commit-config.yaml') -Force
    Copy-Item (Join-Path $root 'templates/python/Taskfile.yml') (Join-Path $Path 'Taskfile.yml') -Force
  }
}

Copy-IfExists (Join-Path $root 'templates/common/.editorconfig') (Join-Path $Path '.editorconfig')
Copy-IfExists (Join-Path $root 'templates/common/.gitattributes') (Join-Path $Path '.gitattributes')

if (Get-Command pre-commit -ErrorAction SilentlyContinue) {
  Push-Location $Path
  pre-commit install
  Pop-Location
} else {
  Write-Host 'pre-commit not installed; skipping hook installation.'
}

Write-Host "Bootstrapped $Type repo at $Path"
