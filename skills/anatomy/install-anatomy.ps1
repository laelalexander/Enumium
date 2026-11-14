<#
.SYNOPSIS
  Installs the "anatomy" skill for Claude Code on Windows, and optionally KiCad.

.DESCRIPTION
  Copies SKILL.md and references\ from this folder (the repo checkout) into
  %USERPROFILE%\.claude\skills\anatomy. If this folder has no SKILL.md but an
  anatomy.skill package sits next to the script, that package is installed instead.
  An existing install is replaced, so files removed upstream do not linger.

  KiCad is only needed for the experimental PCB step (see README.md). It is
  installed with winget unless -SkipKiCad is given.

.PARAMETER SkipKiCad
  Do not check for or install KiCad.

.PARAMETER Package
  Also build anatomy.skill (a zip with an anatomy\ root folder) next to this script.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\install-anatomy.ps1
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\install-anatomy.ps1 -SkipKiCad
#>
[CmdletBinding()]
param(
  [switch]$SkipKiCad,
  [switch]$Package
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version 2.0

# Works on Windows PowerShell 5.1 and PowerShell 7+.
$here = $PSScriptRoot
if (-not $here) { $here = (Get-Location).Path }

$home_ = $env:USERPROFILE
if (-not $home_) { $home_ = [Environment]::GetFolderPath("UserProfile") }
$skillsRoot = Join-Path $home_ ".claude\skills"
$target     = Join-Path $skillsRoot "anatomy"

# Files that make up the installed skill. evals\, README, HANDOFF and this script stay in the repo.
$skillItems = @("SKILL.md", "references")

function Copy-SkillFrom([string]$src, [string]$dest) {
  New-Item -ItemType Directory -Force -Path $dest | Out-Null
  foreach ($item in $skillItems) {
    $p = Join-Path $src $item
    if (-not (Test-Path -LiteralPath $p)) { throw "Missing $item in $src" }
    Copy-Item -LiteralPath $p -Destination $dest -Recurse -Force
  }
}

# --- 1. Install the skill ---------------------------------------------------
$sourceSkill = Join-Path $here "SKILL.md"
$packageFile = Join-Path $here "anatomy.skill"
$staging = Join-Path ([IO.Path]::GetTempPath()) ("anatomy-" + [Guid]::NewGuid().ToString("N"))

try {
  if (Test-Path -LiteralPath $sourceSkill) {
    Write-Host "Installing from source folder $here"
    Copy-SkillFrom $here (Join-Path $staging "anatomy")
  }
  elseif (Test-Path -LiteralPath $packageFile) {
    Write-Host "Installing from package $packageFile"
    # Expand-Archive on Windows PowerShell 5.1 only accepts a .zip extension.
    New-Item -ItemType Directory -Force -Path $staging | Out-Null
    $zip = Join-Path $staging "anatomy.zip"
    Copy-Item -LiteralPath $packageFile -Destination $zip -Force
    Expand-Archive -LiteralPath $zip -DestinationPath $staging -Force
    if (-not (Test-Path -LiteralPath (Join-Path $staging "anatomy\SKILL.md"))) {
      throw "anatomy.skill does not contain anatomy\SKILL.md"
    }
  }
  else {
    throw "Neither SKILL.md nor anatomy.skill found next to this script ($here)."
  }

  New-Item -ItemType Directory -Force -Path $skillsRoot | Out-Null
  if (Test-Path -LiteralPath $target) {
    Write-Host "Replacing existing install at $target"
    Remove-Item -LiteralPath $target -Recurse -Force
  }
  Move-Item -LiteralPath (Join-Path $staging "anatomy") -Destination $target
  Write-Host "Skill installed to $target" -ForegroundColor Green

  if ($Package -and (Test-Path -LiteralPath $sourceSkill)) {
    $pkgStage = Join-Path $staging "pkg"
    Copy-SkillFrom $here (Join-Path $pkgStage "anatomy")
    $tmpZip = Join-Path $staging "anatomy.zip"
    Compress-Archive -Path (Join-Path $pkgStage "anatomy") -DestinationPath $tmpZip -Force
    Copy-Item -LiteralPath $tmpZip -Destination $packageFile -Force
    Write-Host "Built $packageFile"
  }
}
finally {
  if (Test-Path -LiteralPath $staging) { Remove-Item -LiteralPath $staging -Recurse -Force -ErrorAction SilentlyContinue }
}

# --- 2. KiCad (optional, experimental PCB step) -----------------------------
function Find-KiCadCli {
  $cmd = Get-Command kicad-cli -ErrorAction SilentlyContinue
  if ($cmd) { return $cmd.Source }
  $bases = @($env:ProgramFiles, ${env:ProgramFiles(x86)})
  if ($env:LOCALAPPDATA) { $bases += (Join-Path $env:LOCALAPPDATA "Programs") }
  $roots = $bases | Where-Object { $_ } | ForEach-Object { Join-Path $_ "KiCad" }
  foreach ($r in $roots) {
    if (Test-Path -LiteralPath $r) {
      # KiCad installs into a version folder, e.g. C:\Program Files\KiCad\8.0\bin\kicad-cli.exe
      $hit = Get-ChildItem -LiteralPath $r -Directory -ErrorAction SilentlyContinue |
             Sort-Object { try { [version]$_.Name } catch { [version]"0.0" } } -Descending |
             ForEach-Object { Join-Path $_.FullName "bin\kicad-cli.exe" } |
             Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
      if ($hit) { return $hit }
    }
  }
  return $null
}

if ($SkipKiCad) {
  Write-Host "Skipping KiCad (-SkipKiCad)."
}
else {
  $cli = Find-KiCadCli
  if (-not $cli) {
    if (Get-Command winget -ErrorAction SilentlyContinue) {
      Write-Host "KiCad not found. Installing KiCad via winget (this can take a few minutes)..."
      winget install --id KiCad.KiCad -e --accept-package-agreements --accept-source-agreements
      if ($LASTEXITCODE -ne 0) {
        Write-Warning "winget exited with code $LASTEXITCODE. Install KiCad 8+ from https://www.kicad.org/download/windows/ if it did not install."
      }
      $cli = Find-KiCadCli
    }
    else {
      Write-Warning "winget is not available. Install KiCad 8+ from https://www.kicad.org/download/windows/ (only needed for the experimental PCB step)."
    }
  }

  if ($cli) {
    $ver = (& $cli version 2>$null | Select-Object -First 1)
    Write-Host "KiCad found: $cli $ver" -ForegroundColor Green
    $bin = Split-Path -Parent $cli
    $py  = Join-Path $bin "python.exe"
    if (Test-Path -LiteralPath $py) { Write-Host "KiCad Python (has pcbnew): $py" }
    if (-not (Get-Command kicad-cli -ErrorAction SilentlyContinue)) {
      Write-Host "Note: kicad-cli is not on PATH. Claude can call it by full path, or add $bin to PATH."
    }
    if (-not (Get-Command java -ErrorAction SilentlyContinue)) {
      Write-Host "Note: Java not found. Freerouting (optional autorouter) needs it: winget install EclipseAdoptium.Temurin.21.JRE"
    }
  }
}

Write-Host ""
Write-Host "Done. Start Claude Code and ask it to run anatomy on a product."
Write-Host "The KiCad PCB step is experimental and untested; see README.md."
