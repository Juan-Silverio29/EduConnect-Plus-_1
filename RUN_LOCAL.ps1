# RUN_LOCAL.ps1 — Arranca EduConnect+ en local
Set-Location $PSScriptRoot
if (-not (Test-Path ".\venv\Scripts\python.exe")) {
    Write-Host "Creando venv e instalando dependencias..." -ForegroundColor Yellow
    python -m venv venv
    .\venv\Scripts\pip.exe install -r requirements.txt requests
    .\venv\Scripts\python.exe manage.py migrate
}
Write-Host "EduConnect+ en http://127.0.0.1:8000  (Ctrl+C para detener)" -ForegroundColor Green
Write-Host "Usuarios: admin/Admin123! | profesor_demo/Profe123! | estudiante_demo/Estudio123!"
.\venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
