$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot

function Stop-VisualizadorProcess {
    param (
        [int]$ProcessId
    )

    if ($ProcessId -le 0) {
        return
    }

    $process = Get-CimInstance Win32_Process -Filter "ProcessId = $ProcessId" -ErrorAction SilentlyContinue
    if (-not $process) {
        return
    }

    $executablePath = $process.ExecutablePath
    if (-not $executablePath) {
        return
    }

    $normalizedPath = [System.IO.Path]::GetFullPath($executablePath)
    if ($normalizedPath -notlike "$projectRoot*") {
        return
    }

    Stop-Process -Id $ProcessId -Force -ErrorAction SilentlyContinue
}

$listeners = Get-NetTCPConnection -LocalPort 8501 -State Listen -ErrorAction SilentlyContinue
foreach ($listener in $listeners) {
    Stop-VisualizadorProcess -ProcessId $listener.OwningProcess
}

$projectProcesses = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
    $_.ExecutablePath -like "$projectRoot*" -and
    ($_.Name -ieq "python.exe" -or $_.Name -ieq "pythonw.exe")
}

foreach ($process in $projectProcesses) {
    Stop-VisualizadorProcess -ProcessId $process.ProcessId
}
