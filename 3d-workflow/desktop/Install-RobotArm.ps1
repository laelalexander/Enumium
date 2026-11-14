# Installs the Robot Arm app for the current user (no admin rights needed):
#   copies it to %LOCALAPPDATA%\Programs\RobotArm, installs Node.js LTS with winget if it is missing,
#   and adds "Robot Arm" icons to the desktop and the Start menu. Re-running it updates the app in place.
param([switch]$NoLaunch, [switch]$Quiet)
$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Windows.Forms
$src  = $PSScriptRoot
$dest = Join-Path $env:LOCALAPPDATA "Programs\RobotArm"
function Say($m, $icon = "Information") { if (-not $Quiet) { [System.Windows.Forms.MessageBox]::Show($m, "Robot Arm", "OK", $icon) | Out-Null } else { Write-Host $m } }
try {
  # stop a running copy so its files can be replaced
  Get-CimInstance Win32_Process -Filter "Name='node.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like "*RobotArm*server.js*" } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
  $node = (Get-Command node -ErrorAction SilentlyContinue) -or (Test-Path "$env:ProgramFiles\nodejs\node.exe")
  if (-not $node) {
    if (Get-Command winget -ErrorAction SilentlyContinue) {
      winget install --id OpenJS.NodeJS.LTS -e --silent --accept-package-agreements --accept-source-agreements | Out-Null
    } else { Say "Node.js is needed. Install Node.js LTS from nodejs.org, then run this installer again." "Warning"; exit 1 }
  }
  New-Item -ItemType Directory -Force -Path $dest | Out-Null
  if (Test-Path (Join-Path $dest "app")) { Remove-Item -Recurse -Force (Join-Path $dest "app") }   # keeps window\ (your Arduino port permission)
  foreach ($f in @("server.js", "Start-RobotArm.ps1", "RobotArm.vbs", "robot-arm.ico", "Uninstall-RobotArm.ps1", "README.txt")) {
    Copy-Item -LiteralPath (Join-Path $src $f) -Destination $dest -Force
  }
  Copy-Item -LiteralPath (Join-Path $src "app") -Destination $dest -Recurse -Force
  $shell = New-Object -ComObject WScript.Shell
  foreach ($place in @([Environment]::GetFolderPath("Desktop"), [Environment]::GetFolderPath("Programs"))) {
    $lnk = $shell.CreateShortcut((Join-Path $place "Robot Arm.lnk"))
    $lnk.TargetPath = Join-Path $env:SystemRoot "System32\wscript.exe"
    $lnk.Arguments = "`"$(Join-Path $dest 'RobotArm.vbs')`""
    $lnk.WorkingDirectory = $dest
    $lnk.IconLocation = (Join-Path $dest "robot-arm.ico") + ",0"
    $lnk.Description = "Robot arm: 3D test table, drawings, assembly guide and Arduino control"
    $lnk.Save()
  }
  if (-not $NoLaunch) { Start-Process (Join-Path $env:SystemRoot "System32\wscript.exe") "`"$(Join-Path $dest 'RobotArm.vbs')`"" }
  Say "Robot Arm is installed. Open it any time from the Robot Arm icon on your desktop or in the Start menu."
} catch { Say ("Install failed: " + $_.Exception.Message) "Error"; exit 1 }
