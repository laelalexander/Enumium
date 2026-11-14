# Starts the Robot Arm app: runs the local server (hidden) if it is not already up,
# then opens the app in its own window (Microsoft Edge app mode: no tabs, no address bar).
# Edge is used because it supports Web Serial, which the Link tab needs to talk to the Arduino.
param([int]$Port = 8766)
$ErrorActionPreference = "Stop"
$here = $PSScriptRoot
$url  = "http://127.0.0.1:$Port/control/index.html"
Add-Type -AssemblyName System.Windows.Forms

function Test-Up { try { (Invoke-RestMethod -Uri "http://127.0.0.1:$Port/api/health" -TimeoutSec 2).app -eq "robot-arm" } catch { $false } }
function Find-Node {
  $c = Get-Command node -ErrorAction SilentlyContinue
  if ($c) { return $c.Source }
  foreach ($p in @("$env:ProgramFiles\nodejs\node.exe", "${env:ProgramFiles(x86)}\nodejs\node.exe", "$env:LOCALAPPDATA\Programs\nodejs\node.exe")) {
    if ($p -and (Test-Path -LiteralPath $p)) { return $p }
  }
  return $null
}

if (-not (Test-Up)) {
  $node = Find-Node
  if (-not $node) {
    [System.Windows.Forms.MessageBox]::Show("Robot Arm needs Node.js. Run the installer again, or install Node.js LTS from nodejs.org.", "Robot Arm", "OK", "Warning") | Out-Null
    exit 1
  }
  $env:ROBOT_ARM_PORT = "$Port"
  Start-Process -FilePath $node -ArgumentList "`"$(Join-Path $here 'server.js')`"" -WorkingDirectory $here -WindowStyle Hidden `
    -RedirectStandardOutput (Join-Path $here "server.log") -RedirectStandardError (Join-Path $here "server.err.log")
  $ok = $false
  for ($i = 0; $i -lt 40; $i++) { Start-Sleep -Milliseconds 250; if (Test-Up) { $ok = $true; break } }
  if (-not $ok) {
    [System.Windows.Forms.MessageBox]::Show("Robot Arm could not start. Details: $here\server.err.log", "Robot Arm", "OK", "Error") | Out-Null
    exit 1
  }
}

$edge = @("${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe", "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe") |
  Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -First 1
if ($edge) {
  # Own profile folder: the app gets its own window and taskbar entry, and keeps its Arduino port permission.
  Start-Process -FilePath $edge -ArgumentList @("--app=$url", "--user-data-dir=`"$(Join-Path $here 'window')`"", "--window-size=1600,950",
    "--no-first-run", "--no-default-browser-check", "--disable-sync", "--disable-extensions", "--disable-features=msImplicitSignin,msEdgeSyncConsent")
} else {
  Start-Process $url
}
