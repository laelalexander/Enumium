<#
.SYNOPSIS
  Anatomy launcher: pick or create a project in C:\Anatomy and open Claude Code in it.

.DESCRIPTION
  Shows a small window listing the projects under the Anatomy root folder.
  "New project" creates a folder, writes a CLAUDE.md that points Claude at the
  anatomy skill, and opens Claude Code there. "Open" reopens an existing project.
  Started from the "Anatomy" desktop icon that install-anatomy.ps1 creates.

.PARAMETER Root
  Folder that holds projects. Default C:\Anatomy.
#>
param(
  [string]$Root = "C:\Anatomy"
)

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
[System.Windows.Forms.Application]::EnableVisualStyles()

New-Item -ItemType Directory -Force -Path $Root | Out-Null

function Get-Slug([string]$name) {
  $s = $name.ToLowerInvariant() -replace '[^a-z0-9]+', '-'
  return $s.Trim('-')
}

function Find-Claude {
  $c = Get-Command claude -ErrorAction SilentlyContinue
  if ($c) { return $c.Source }
  foreach ($p in @(
      (Join-Path $env:USERPROFILE ".local\bin\claude.exe"),
      (Join-Path $env:APPDATA "npm\claude.cmd"))) {
    if ($p -and (Test-Path -LiteralPath $p)) { return $p }
  }
  return $null
}

function Write-ProjectFiles([string]$dir, [string]$name, [string]$kind, [string]$brief) {
  New-Item -ItemType Directory -Force -Path $dir | Out-Null
  $claudeMd = Join-Path $dir "CLAUDE.md"
  if (-not (Test-Path -LiteralPath $claudeMd)) {
    $text = @"
# Anatomy project: $name

This folder is an Anatomy project. Use the ``anatomy`` skill for all work here.

- Product type: $kind
- Brief: $brief
- Put the blueprint and prototype in this folder (``anatomy-<slug>/`` as the skill describes).
- Datasheets and reference files the user adds go in ``inputs/``. Read them before relying on memory for pinouts or part numbers.
- The KiCad PCB step is experimental. Find KiCad under ``C:\Program Files\KiCad\<version>\bin`` if ``kicad-cli`` is not on PATH, run ERC and DRC, and stop and say so if KiCad cannot run.
"@
    Set-Content -LiteralPath $claudeMd -Value $text -Encoding UTF8
  }
  New-Item -ItemType Directory -Force -Path (Join-Path $dir "inputs") | Out-Null
  $meta = Join-Path $dir "anatomy-project.json"
  if (-not (Test-Path -LiteralPath $meta)) {
    @{ name = $name; kind = $kind; brief = $brief; created = (Get-Date).ToString("s") } |
      ConvertTo-Json | Set-Content -LiteralPath $meta -Encoding UTF8
  }
}

function Open-Claude([string]$dir, [string]$firstPrompt) {
  $claude = Find-Claude
  if (-not $claude) {
    [System.Windows.Forms.MessageBox]::Show(
      "Claude Code is not installed or not on PATH.`r`nInstall it from https://claude.com/claude-code, then try again.",
      "Anatomy", "OK", "Warning") | Out-Null
    return
  }
  # Build the command run inside the new window. Single quotes are escaped for PowerShell.
  $q = { param($s) "'" + ($s -replace "'", "''") + "'" }
  $cmd = "Set-Location -LiteralPath $(& $q $dir); & $(& $q $claude)"
  if ($firstPrompt) { $cmd += " $(& $q $firstPrompt)" }

  # -EncodedCommand avoids quoting problems, and Windows Terminal treats ';' as its own separator.
  $enc = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($cmd))
  $wt = Get-Command wt -ErrorAction SilentlyContinue
  if ($wt) {
    Start-Process wt -ArgumentList @("-d", "`"$dir`"", "powershell", "-NoExit", "-EncodedCommand", $enc)
  } else {
    Start-Process powershell -WorkingDirectory $dir -ArgumentList @("-NoExit", "-EncodedCommand", $enc)
  }
}

# ---------------------------------------------------------------- UI
$form = New-Object System.Windows.Forms.Form
$form.Text = "Anatomy"
$form.Size = New-Object System.Drawing.Size(560, 520)
$form.StartPosition = "CenterScreen"
$form.Font = New-Object System.Drawing.Font("Segoe UI", 10)

$lblList = New-Object System.Windows.Forms.Label
$lblList.Text = "Projects in $Root"
$lblList.Location = "16,12"; $lblList.AutoSize = $true
$form.Controls.Add($lblList)

$list = New-Object System.Windows.Forms.ListBox
$list.Location = "16,36"; $list.Size = "510,150"
$form.Controls.Add($list)

$btnOpen = New-Object System.Windows.Forms.Button
$btnOpen.Text = "Open in Claude"; $btnOpen.Location = "16,192"; $btnOpen.Size = "150,32"
$form.Controls.Add($btnOpen)

$btnFolder = New-Object System.Windows.Forms.Button
$btnFolder.Text = "Show folder"; $btnFolder.Location = "176,192"; $btnFolder.Size = "120,32"
$form.Controls.Add($btnFolder)

$grp = New-Object System.Windows.Forms.GroupBox
$grp.Text = "New project"; $grp.Location = "16,236"; $grp.Size = "510,230"
$form.Controls.Add($grp)

$lblName = New-Object System.Windows.Forms.Label
$lblName.Text = "Name"; $lblName.Location = "12,28"; $lblName.AutoSize = $true
$grp.Controls.Add($lblName)
$txtName = New-Object System.Windows.Forms.TextBox
$txtName.Location = "110,24"; $txtName.Size = "385,26"
$grp.Controls.Add($txtName)

$lblKind = New-Object System.Windows.Forms.Label
$lblKind.Text = "Type"; $lblKind.Location = "12,62"; $lblKind.AutoSize = $true
$grp.Controls.Add($lblKind)
$cmbKind = New-Object System.Windows.Forms.ComboBox
$cmbKind.DropDownStyle = "DropDownList"
$cmbKind.Location = "110,58"; $cmbKind.Size = "385,26"
@("Hardware product", "Web app or website", "Repo or library", "CLI or desktop tool", "API") |
  ForEach-Object { [void]$cmbKind.Items.Add($_) }
$cmbKind.SelectedIndex = 0
$grp.Controls.Add($cmbKind)

$lblBrief = New-Object System.Windows.Forms.Label
$lblBrief.Text = "What to build"; $lblBrief.Location = "12,96"; $lblBrief.AutoSize = $true
$grp.Controls.Add($lblBrief)
$txtBrief = New-Object System.Windows.Forms.TextBox
$txtBrief.Multiline = $true; $txtBrief.ScrollBars = "Vertical"
$txtBrief.Location = "110,92"; $txtBrief.Size = "385,80"
$txtBrief.Text = "7.5 inch e-ink desk display: calendar and weather over wifi, battery powered"
$grp.Controls.Add($txtBrief)

$btnCreate = New-Object System.Windows.Forms.Button
$btnCreate.Text = "Create and start"; $btnCreate.Location = "110,182"; $btnCreate.Size = "160,32"
$grp.Controls.Add($btnCreate)

function Refresh-List {
  $list.Items.Clear()
  Get-ChildItem -LiteralPath $Root -Directory |
    Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName "CLAUDE.md") } |
    Sort-Object LastWriteTime -Descending |
    ForEach-Object { [void]$list.Items.Add($_.Name) }
  $btnOpen.Enabled = $list.Items.Count -gt 0
  $btnFolder.Enabled = $list.Items.Count -gt 0
  if ($list.Items.Count -gt 0) { $list.SelectedIndex = 0 }
}

$openSelected = {
  if ($list.SelectedItem) { Open-Claude (Join-Path $Root $list.SelectedItem) $null }
}
$btnOpen.Add_Click($openSelected)
$list.Add_DoubleClick($openSelected)
$btnFolder.Add_Click({
  if ($list.SelectedItem) { Start-Process explorer.exe (Join-Path $Root $list.SelectedItem) }
})

$btnCreate.Add_Click({
  $name = $txtName.Text.Trim()
  if (-not $name) { $name = $txtBrief.Text.Trim() }
  $slug = Get-Slug $name
  if (-not $slug) {
    [System.Windows.Forms.MessageBox]::Show("Give the project a name.", "Anatomy") | Out-Null
    return
  }
  if ($slug.Length -gt 40) { $slug = $slug.Substring(0, 40).Trim('-') }
  $dir = Join-Path $Root $slug
  $isNew = -not (Test-Path -LiteralPath $dir)
  Write-ProjectFiles $dir $name $cmbKind.SelectedItem $txtBrief.Text.Trim()
  Refresh-List
  $prompt = $null
  if ($isNew) {
    $prompt = "Run the anatomy skill on this project: $($txtBrief.Text.Trim()) (type: $($cmbKind.SelectedItem)). " +
              "Read CLAUDE.md and anything in inputs/ first."
  }
  Open-Claude $dir $prompt
})

Refresh-List
[void]$form.ShowDialog()
