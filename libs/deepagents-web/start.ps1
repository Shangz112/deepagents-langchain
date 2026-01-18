$ErrorActionPreference = "Stop"

# Get script directory to ensure we run from the correct location
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $ScriptDir

# Default configuration
$PythonPort = 8001
$ServerPort = 8005
$WebPort = 5173
$PyServiceUrl = "http://127.0.0.1:8001"
$EnvFile = ".env"

# Load .env variables if file exists
if (Test-Path $EnvFile) {
    Write-Host "Loading configuration from $EnvFile..."
    Get-Content $EnvFile | ForEach-Object {
        if ($_ -match '^\s*([^#=]+)\s*=\s*(.*)$') {
            $Key = $matches[1].Trim()
            $Value = $matches[2].Trim()
            
            # Set environment variable for current process (and children)
            [Environment]::SetEnvironmentVariable($Key, $Value, "Process")
            
            # Update local variables for command construction
            if ($Key -eq "PYTHON_PORT") { $PythonPort = $Value }
            if ($Key -eq "SERVER_PORT") { $ServerPort = $Value }
            if ($Key -eq "WEB_PORT") { $WebPort = $Value }
            if ($Key -eq "PY_SERVICE_URL") { $PyServiceUrl = $Value }
        }
    }
} else {
    Write-Warning "$EnvFile not found. Using default ports."
}

Write-Host "--------------------------------------------------"
Write-Host "Starting DeepAgents Services..."
Write-Host "--------------------------------------------------"
Write-Host "Python Service: Port $PythonPort"
Write-Host "Node Server:    Port $ServerPort"
Write-Host "Web Client:     Port $WebPort"
Write-Host "--------------------------------------------------"

# Start Python Service
Write-Host "Launching Python Service..."
Start-Process -NoNewWindow powershell -ArgumentList "-Command", "cd services/python; `$env:PYTHON_PORT=$PythonPort; uvicorn app:app --port $PythonPort --host 127.0.0.1 --reload"

# Start Node Server
Write-Host "Launching Node Server..."
Start-Process -NoNewWindow powershell -ArgumentList "-Command", "cd apps/server; `$env:SERVER_PORT=$ServerPort; `$env:PY_SERVICE_URL='$PyServiceUrl'; npm run dev"

# Start Web Client
Write-Host "Launching Web Client..."
Start-Process -NoNewWindow powershell -ArgumentList "-Command", "cd apps/web; `$env:WEB_PORT=$WebPort; npm run dev"

Write-Host "Services started."
