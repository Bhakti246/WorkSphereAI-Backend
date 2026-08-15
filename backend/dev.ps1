# Development helper for WorkSphereAI backend

# Activate venv if it exists
if (Test-Path .\venv\Scripts\Activate.ps1) {
    . .\venv\Scripts\Activate.ps1
} else {
    Write-Host "Virtual environment not found. Create it with: python -m venv venv"
    exit 1
}

# Load environment variables from .env if present
if (Test-Path .env) {
    Get-Content .env | ForEach-Object {
        if ($_ -and $_ -notmatch '^\s*#') {
            $parts = $_ -split '=', 2
            if ($parts.Length -eq 2) {
                [System.Environment]::SetEnvironmentVariable($parts[0].Trim(), $parts[1].Trim(), 'Process')
            }
        }
    }
}

Write-Host "Starting Django development server..."
python manage.py runserver
