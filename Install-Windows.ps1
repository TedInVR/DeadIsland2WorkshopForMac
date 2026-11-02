$ErrorActionPreference = 'Stop'
$source = Join-Path $PSScriptRoot 'Dead Island 2 Workshop'
$target = Join-Path $env:LOCALAPPDATA 'Programs\Dead Island 2 Workshop'
$backup = "$target.previous"
if (-not (Test-Path (Join-Path $source 'Dead Island 2 Workshop.exe'))) { throw 'Extract the complete Windows ZIP before running this installer.' }
$running = Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.Path -eq (Join-Path $target 'Dead Island 2 Workshop.exe') }
if ($running) { throw 'Quit Dead Island 2 Workshop before installing this update.' }
New-Item -ItemType Directory -Force (Split-Path $target) | Out-Null
if (Test-Path $backup) { Remove-Item -Recurse -Force $backup }
if (Test-Path $target) { Move-Item $target $backup }
try {
    Copy-Item -Recurse $source $target
} catch {
    if (Test-Path $target) { Remove-Item -Recurse -Force $target }
    if (Test-Path $backup) { Move-Item $backup $target }
    throw
}
if (Test-Path $backup) { Remove-Item -Recurse -Force $backup }
$shell = New-Object -ComObject WScript.Shell
foreach ($folder in @([Environment]::GetFolderPath('Desktop'), (Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs'))) {
    New-Item -ItemType Directory -Force $folder | Out-Null
    $link = $shell.CreateShortcut((Join-Path $folder 'Dead Island 2 Workshop.lnk'))
    $link.TargetPath = Join-Path $target 'Dead Island 2 Workshop.exe'
    $link.WorkingDirectory = $target
    $link.IconLocation = "$target\Dead Island 2 Workshop.exe,0"
    $link.Save()
}
Write-Host "Installed: $target"
Start-Process (Join-Path $target 'Dead Island 2 Workshop.exe')
