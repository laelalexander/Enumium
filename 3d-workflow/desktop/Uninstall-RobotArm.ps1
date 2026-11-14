# Removes the Robot Arm app and its icons. Your own files elsewhere are not touched.
$dest = $PSScriptRoot     # the installed copy this script sits in (Anatomy project or %LOCALAPPDATA%\Programs\RobotArm)
if (-not (Test-Path (Join-Path $dest "server.js"))) { exit 1 }
Get-CimInstance Win32_Process -Filter "Name='node.exe'" -ErrorAction SilentlyContinue |
  Where-Object { ($_.CommandLine -like "*RobotArm*server.js*" -or $_.CommandLine -like "*robot-arm*server.js*") } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
foreach ($place in @([Environment]::GetFolderPath("Desktop"), [Environment]::GetFolderPath("Programs"))) {
  Remove-Item -LiteralPath (Join-Path $place "Robot Arm.lnk") -ErrorAction SilentlyContinue
}
Start-Sleep -Milliseconds 500
Remove-Item -LiteralPath $dest -Recurse -Force -ErrorAction SilentlyContinue
