# Starts the Anatomy app: runs the local server (hidden) if it is not already up,
# then opens the UI in its own app window (Microsoft Edge app mode, no browser chrome).
param([string]$Root = "C:\Anatomy", [int]$Port = 4377)
$ErrorActionPreference = "Stop"
$here = $PSScriptRoot
$url  = "http://127.0.0.1:$Port/"

function Test-Up {
  try { (Invoke-RestMethod -Uri ($url + "api/health") -TimeoutSec 2).app -eq "anatomy" } catch { $false }
}

function Find-Node {
  $c = Get-Command node -ErrorAction SilentlyContinue
  if ($c) { return $c.Source }
  foreach ($p in @("$env:ProgramFiles\nodejs\node.exe", "${env:ProgramFiles(x86)}\nodejs\node.exe", "$env:LOCALAPPDATA\Programs\nodejs\node.exe")) {
    if ($p -and (Test-Path -LiteralPath $p)) { return $p }
  }
  return $null
}

Add-Type -AssemblyName System.Windows.Forms

if (-not (Test-Up)) {
  $node = Find-Node
  if (-not $node) {
    [System.Windows.Forms.MessageBox]::Show("Anatomy needs Node.js. Re-run install-anatomy.ps1, or install it with: winget install OpenJS.NodeJS.LTS", "Anatomy", "OK", "Warning") | Out-Null
    exit 1
  }
  # Clear markers inherited if this was started from inside a Claude Code session.
  Get-ChildItem Env: | Where-Object { $_.Name -eq 'CLAUDECODE' -or $_.Name -like 'CLAUDE_CODE_*' -or $_.Name -eq 'ANTHROPIC_BASE_URL' } |
    ForEach-Object { Remove-Item -LiteralPath ("Env:" + $_.Name) }
  $env:ANATOMY_ROOT = $Root
  $env:ANATOMY_PORT = "$Port"
  $log = Join-Path $here "server.log"
  Start-Process -FilePath $node -ArgumentList "`"$(Join-Path $here 'server.js')`"" -WorkingDirectory $here `
    -WindowStyle Hidden -RedirectStandardOutput $log -RedirectStandardError (Join-Path $here "server.err.log")
  $ok = $false
  for ($i = 0; $i -lt 40; $i++) { Start-Sleep -Milliseconds 250; if (Test-Up) { $ok = $true; break } }
  if (-not $ok) {
    [System.Windows.Forms.MessageBox]::Show("Anatomy could not start its server. See $here\server.err.log", "Anatomy", "OK", "Error") | Out-Null
    exit 1
  }
}

$edge = @("${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe", "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe") |
  Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -First 1
if ($edge) {
  # A separate profile folder makes Anatomy its own window and taskbar entry.
  # Edge signs new profiles into the Windows account and syncs extensions, which then open
  # their own browser windows; keep this profile bare (no sync, no extensions).
  Start-Process -FilePath $edge -ArgumentList @("--app=$url", "--user-data-dir=`"$(Join-Path $here 'window')`"", "--window-size=1400,900",
    "--no-first-run", "--no-default-browser-check", "--disable-sync", "--disable-extensions", "--disable-features=msImplicitSignin,msEdgeSyncConsent")
} else {
  Start-Process $url
}
