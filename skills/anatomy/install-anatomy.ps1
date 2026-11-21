<#
.SYNOPSIS
  Installs the "anatomy" skill for Claude Code on Windows, and optionally KiCad.

.DESCRIPTION
  Copies SKILL.md, references\ and tools\ from this folder (the repo checkout) into
  %USERPROFILE%\.claude\skills\anatomy. If this folder has no SKILL.md but an
  anatomy.skill package sits next to the script, that package is installed instead.
  An existing install is replaced, so files removed upstream do not linger.

  KiCad is only needed for the experimental PCB step (see README.md). It is
  installed with winget unless -SkipKiCad is given.

.PARAMETER SkipKiCad
  Do not check for or install KiCad.

.PARAMETER NoShortcut
  Do not install the Anatomy app (and Node.js) or its desktop and Start menu icons.

.PARAMETER ProjectsRoot
  Folder the Anatomy app keeps projects in. Default C:\Anatomy.

.PARAMETER Force
  Update even if a project run is in progress (the run is stopped).

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
  [switch]$Package,
  [switch]$NoShortcut,
  [switch]$Force,
  [string]$ProjectsRoot = "C:\Anatomy"
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
$skillItems = @("SKILL.md", "references", "tools")

# Never cut off a project run: refuse to update while one is in progress (unless -Force).
$busy = @()
try {
  $all = Invoke-RestMethod -Uri "http://127.0.0.1:4377/api/projects" -TimeoutSec 2   # PS 5.1 returns a JSON array as one object
  $busy = @($all | ForEach-Object { $_ } | Where-Object { $_.status -eq 'running' })
} catch { }
if ($busy.Count -gt 0 -and -not $Force) {
  throw "Anatomy is running a project ($($busy[0].title)). Wait for it to finish, then run the installer again (or use -Force to stop it)."
}

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

# --- 3. Anatomy app, Node.js, and desktop icon --------------------------------
if (-not $NoShortcut) {
  $appSrc = Join-Path $here "app"
  if (Test-Path -LiteralPath (Join-Path $appSrc "server.js")) {
    # Node.js runs the app's local server.
    $nodeOk = (Get-Command node -ErrorAction SilentlyContinue) -or (Test-Path -LiteralPath "$env:ProgramFiles\nodejs\node.exe")
    if (-not $nodeOk) {
      if (Get-Command winget -ErrorAction SilentlyContinue) {
        Write-Host "Installing Node.js (needed by the Anatomy app) via winget..."
        winget install --id OpenJS.NodeJS.LTS -e --accept-package-agreements --accept-source-agreements
      } else {
        Write-Warning "Node.js is missing and winget is not available. Install Node.js LTS from https://nodejs.org"
      }
    }

    $appDir = Join-Path $env:LOCALAPPDATA "Anatomy"
    New-Item -ItemType Directory -Force -Path $appDir | Out-Null
    # Stop a running Anatomy server so its files can be replaced.
    try { Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:4377/api/quit" -TimeoutSec 2 | Out-Null; Start-Sleep -Milliseconds 600 } catch { }
    $old = Join-Path $appDir "Anatomy.ps1"   # first-version launcher, no longer used
    if (Test-Path -LiteralPath $old) { Remove-Item -LiteralPath $old -Force }
    foreach ($f in @("server.js", "xometry.js", "sync.js", "models.js", "design.js", "Start-Anatomy.ps1", "Anatomy.vbs", "anatomy.ico")) {
      Copy-Item -LiteralPath (Join-Path $appSrc $f) -Destination $appDir -Force
    }
    $pub = Join-Path $appDir "public"
    if (Test-Path -LiteralPath $pub) { Remove-Item -LiteralPath $pub -Recurse -Force }
    Copy-Item -LiteralPath (Join-Path $appSrc "public") -Destination $appDir -Recurse -Force
    $bl = Join-Path $appDir "blender"
    if (Test-Path -LiteralPath $bl) { Remove-Item -LiteralPath $bl -Recurse -Force }
    Copy-Item -LiteralPath (Join-Path $appSrc "blender") -Destination $appDir -Recurse -Force
    $refs = Join-Path $appDir "skill-refs"
    New-Item -ItemType Directory -Force -Path $refs | Out-Null
    foreach ($f in @("industrial-design.md", "design-revisions.md", "precision-engineering.md")) { Copy-Item -LiteralPath (Join-Path $PSScriptRoot "references\$f") -Destination $refs -Force }
    $eng = Join-Path $appDir "eng-tools"
    New-Item -ItemType Directory -Force -Path $eng | Out-Null
    foreach ($f in @("check_engineering.py", "step_features.py")) { Copy-Item -LiteralPath (Join-Path $PSScriptRoot "tools\eng\$f") -Destination $eng -Force }
    New-Item -ItemType Directory -Force -Path $ProjectsRoot | Out-Null

    $shell = New-Object -ComObject WScript.Shell
    foreach ($place in @([Environment]::GetFolderPath("Desktop"), [Environment]::GetFolderPath("Programs"))) {
      $lnk = $shell.CreateShortcut((Join-Path $place "Anatomy.lnk"))
      $lnk.TargetPath = Join-Path $env:SystemRoot "System32\wscript.exe"
      $lnk.Arguments = "`"$(Join-Path $appDir 'Anatomy.vbs')`" `"$ProjectsRoot`""
      $lnk.WorkingDirectory = $appDir
      $lnk.IconLocation = (Join-Path $appDir "anatomy.ico") + ",0"
      $lnk.Description = "Anatomy: dissect and rebuild a product"
      $lnk.Save()
    }
    Write-Host "Anatomy app installed. Open it from the Anatomy icon on your desktop or Start menu." -ForegroundColor Green
  }
  if (-not (Get-Command claude -ErrorAction SilentlyContinue) -and -not (Test-Path -LiteralPath (Join-Path $home_ ".local\bin\claude.exe"))) {
    Write-Warning "Claude Code (claude) was not found. The Anatomy app needs it: https://claude.com/claude-code"
  }
}

Write-Host ""
Write-Host "Done. Double-click the Anatomy icon on your desktop to start a project."
Write-Host "The KiCad PCB step is experimental and untested; see README.md."
