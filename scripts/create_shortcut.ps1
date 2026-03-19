param(
    [string]$TargetPath = "",
    [string]$ShortcutPath = "",
    [string]$IconPath = "",
    [string]$WorkingDirectory = ""
)

$projectRoot = Split-Path -Parent $PSScriptRoot

if ([string]::IsNullOrWhiteSpace($TargetPath)) {
    $TargetPath = Join-Path $projectRoot "INICIAR.bat"
}

if ([string]::IsNullOrWhiteSpace($ShortcutPath)) {
    $desktop = [Environment]::GetFolderPath("Desktop")
    $ShortcutPath = Join-Path $desktop "Visualizador Telepase.lnk"
}

if ([string]::IsNullOrWhiteSpace($IconPath)) {
    $IconPath = Join-Path $projectRoot "antena.ico"
}

if ([string]::IsNullOrWhiteSpace($WorkingDirectory)) {
    $WorkingDirectory = $projectRoot
}

if (-not (Test-Path $TargetPath)) {
    throw "No se encontro el archivo objetivo: $TargetPath"
}

if (-not (Test-Path $IconPath)) {
    throw "No se encontro el icono: $IconPath"
}

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($ShortcutPath)
$shortcut.TargetPath = $TargetPath
$shortcut.WorkingDirectory = $WorkingDirectory
$shortcut.IconLocation = $IconPath
$shortcut.WindowStyle = 1
$shortcut.Description = "Visualizador Telepase"
$shortcut.Save()

Write-Host "Acceso directo creado en: $ShortcutPath"
