param(
    [string]$Version = "v1.0.0"
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$packageRoot = Join-Path $projectRoot "dist"
$packageName = "VisualizadorTelepase_$Version"
$packageDir = Join-Path $packageRoot $packageName
$zipPath = Join-Path $packageRoot ($packageName + ".zip")

$requiredPaths = @(
    "app.py",
    "app_logic.py",
    "app_logging.py",
    "etl.py",
    "INICIAR.bat",
    "run_telepase.bat",
    "ACTUALIZAR_SISTEMA.bat",
    "VERIFICAR_SISTEMA.bat",
    "CREAR_ACCESO_DIRECTO.bat",
    "README.md",
    "DEPLOYMENT.md",
    "MANUAL_USUARIO.md",
    "RELEASE_NOTES_v1.0.0.md",
    "requirements.txt",
    "antena.ico",
    "demo.png",
    "scripts",
    "src",
    "Sistema_Python"
)

foreach ($path in $requiredPaths) {
    $fullPath = Join-Path $projectRoot $path
    if (-not (Test-Path $fullPath)) {
        throw "No se encontro el recurso requerido: $path"
    }
}

New-Item -ItemType Directory -Force -Path $packageRoot | Out-Null

if (Test-Path $packageDir) {
    Remove-Item -Recurse -Force $packageDir
}

if (Test-Path $zipPath) {
    Remove-Item -Force $zipPath
}

New-Item -ItemType Directory -Force -Path $packageDir | Out-Null

$copyPaths = @(
    "app.py",
    "app_logic.py",
    "app_logging.py",
    "etl.py",
    "INICIAR.bat",
    "run_telepase.bat",
    "ACTUALIZAR_SISTEMA.bat",
    "VERIFICAR_SISTEMA.bat",
    "CREAR_ACCESO_DIRECTO.bat",
    "README.md",
    "DEPLOYMENT.md",
    "MANUAL_USUARIO.md",
    "RELEASE_NOTES_v1.0.0.md",
    "requirements.txt",
    "antena.ico",
    "demo.png"
)

foreach ($path in $copyPaths) {
    Copy-Item -Path (Join-Path $projectRoot $path) -Destination (Join-Path $packageDir $path) -Force
}

Copy-Item -Path (Join-Path $projectRoot "scripts") -Destination (Join-Path $packageDir "scripts") -Recurse -Force
Copy-Item -Path (Join-Path $projectRoot "src") -Destination (Join-Path $packageDir "src") -Recurse -Force
Copy-Item -Path (Join-Path $projectRoot "Sistema_Python") -Destination (Join-Path $packageDir "Sistema_Python") -Recurse -Force

Compress-Archive -Path $packageDir -DestinationPath $zipPath -Force

Write-Host "Paquete generado en: $packageDir"
Write-Host "Zip generado en: $zipPath"
