# RUN_LOCAL.ps1 — Arranca EduConnect+ en local
Set-Location $PSScriptRoot
if (-not (Test-Path ".\venv\Scripts\python.exe")) {
    Write-Host "Creando venv e instalando dependencias..." -ForegroundColor Yellow
    python -m venv venv
    .\venv\Scripts\pip.exe install -r requirements.txt requests
}

$dbPath = Join-Path $PSScriptRoot "db.sqlite3"
$needsDbReset = $false
if (Test-Path $dbPath) {
    try {
        $schemaCheck = .\venv\Scripts\python.exe -c "import sqlite3; conn = sqlite3.connect('db.sqlite3'); cols = [col[1] for col in conn.execute('PRAGMA table_info(auth_app_perfilusuario)')]; print('equipo_id' in cols); conn.close()"
        if ($schemaCheck.Trim() -ne 'True') {
            $needsDbReset = $true
        }
    }
    catch {
        $needsDbReset = $true
    }
}

if ($needsDbReset) {
    Write-Host "Base de datos local desactualizada: recreando schema y datos demo..." -ForegroundColor Yellow
    Remove-Item $dbPath -Force -ErrorAction SilentlyContinue
}

Write-Host "Aplicando migraciones de Django..." -ForegroundColor Yellow
.\venv\Scripts\python.exe manage.py migrate --noinput

Write-Host "Creando usuarios y contenido demo si no existen..." -ForegroundColor Yellow
.\venv\Scripts\python.exe crear_cursos_demo.py

Write-Host "EduConnect+ en http://127.0.0.1:8000  (Ctrl+C para detener)" -ForegroundColor Green
Write-Host "Usuarios: admin/Admin123! | profesor_demo/Profe123! | estudiante_demo/Estudio123!"
.\venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
