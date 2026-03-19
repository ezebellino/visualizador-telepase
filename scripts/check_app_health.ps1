param(
    [string]$Url = "http://127.0.0.1:8501",
    [int]$TimeoutSeconds = 5
)

try {
    $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec $TimeoutSeconds
    if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 400) {
        Write-Host "OK: la aplicacion responde en $Url"
        exit 0
    }

    Write-Host "ERROR: la aplicacion respondio con estado $($response.StatusCode)"
    exit 1
}
catch {
    Write-Host "ERROR: no se pudo conectar con $Url"
    exit 1
}
