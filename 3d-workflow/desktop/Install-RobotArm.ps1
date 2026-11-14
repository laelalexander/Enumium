# Installs the Robot Arm app for the current user (no admin rights needed):
#   copies it to C:\Anatomy\robot-arm (Anatomy project) or %LOCALAPPDATA%\Programs\RobotArm, installs Node.js LTS with winget if it is missing,
#   and adds "Robot Arm" icons to the desktop and the Start menu. Re-running it updates the app in place.
param([switch]$NoLaunch, [switch]$Quiet)
$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Windows.Forms
$src  = $PSScriptRoot
# With the Anatomy app on this PC (C:\Anatomy or %ANATOMY_ROOT%), the app installs as the Anatomy project "robot-arm",
# so Anatomy lists it, runs it and shows it in its live 3D viewer. Otherwise it goes to %LOCALAPPDATA%\Programs\RobotArm.
$anatomyRoot = if ($env:ANATOMY_ROOT) { $env:ANATOMY_ROOT } else { "C:\Anatomy" }
$dest = if (Test-Path $anatomyRoot) { Join-Path $anatomyRoot "robot-arm" } else { Join-Path $env:LOCALAPPDATA "Programs\RobotArm" }
function Say($m, $icon = "Information") { if (-not $Quiet) { [System.Windows.Forms.MessageBox]::Show($m, "Robot Arm", "OK", $icon) | Out-Null } else { Write-Host $m } }
try {
  # stop a running copy so its files can be replaced
  Get-CimInstance Win32_Process -Filter "Name='node.exe'" -ErrorAction SilentlyContinue |
    Where-Object { ($_.CommandLine -like "*RobotArm*server.js*" -or $_.CommandLine -like "*robot-arm*server.js*") } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
  $node = (Get-Command node -ErrorAction SilentlyContinue) -or (Test-Path "$env:ProgramFiles\nodejs\node.exe")
  if (-not $node) {
    if (Get-Command winget -ErrorAction SilentlyContinue) {
      winget install --id OpenJS.NodeJS.LTS -e --silent --accept-package-agreements --accept-source-agreements | Out-Null
    } else { Say "Node.js is needed. Install Node.js LTS from nodejs.org, then run this installer again." "Warning"; exit 1 }
  }
  New-Item -ItemType Directory -Force -Path $dest | Out-Null
  foreach ($d in @("app", "docs", "build")) { if (Test-Path (Join-Path $dest $d)) { Remove-Item -Recurse -Force (Join-Path $dest $d) } }   # keeps window\ and venv\
  foreach ($f in @("server.js", "Start-RobotArm.ps1", "RobotArm.vbs", "robot-arm.ico", "Uninstall-RobotArm.ps1", "README.txt", "anatomy.json", "CLAUDE.md")) {
    Copy-Item -LiteralPath (Join-Path $src $f) -Destination $dest -Force
  }
  Copy-Item -LiteralPath (Join-Path $src "app") -Destination $dest -Recurse -Force
  Copy-Item -LiteralPath (Join-Path $src "docs") -Destination $dest -Recurse -Force
  if (Test-Path (Join-Path $src "build")) { Copy-Item -LiteralPath (Join-Path $src "build") -Destination $dest -Recurse -Force }
  if (Test-Path $anatomyRoot) {                     # register with Anatomy (keeps its own history if already there)
    $meta = Join-Path $dest ".anatomy\project.json"
    $now = (Get-Date).ToUniversalTime().ToString("o")
    if (Test-Path $meta) { $m = Get-Content $meta -Raw | ConvertFrom-Json; $m.updated = $now }
    else { New-Item -ItemType Directory -Force -Path (Split-Path $meta) | Out-Null
           $m = [ordered]@{ title = "Robot arm test table"; status = "done"; created = $now; updated = $now; model = "";
                            prompt = "4-DOF desktop robot arm test table: 5 lb payload, 39.4 in reach. Finished prototype standard: complete build package (drawings, cut files, G-code, purchase list, assembly guide, wiring, firmware) and a Build wizard." } }
    [IO.File]::WriteAllText($meta, ($m | ConvertTo-Json), (New-Object Text.UTF8Encoding $false))   # no BOM: Node JSON.parse rejects it
  }
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
