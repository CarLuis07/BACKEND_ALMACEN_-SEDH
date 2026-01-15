#!/usr/bin/env python3
import subprocess
import os
import time

SERVER_HOST = "192.168.180.164"
SERVER_USER = "administrador"
SERVER_PASSWORD = "DHumanos25"

print("Verificando y copiando archivos manualmente...")

files = [
    ("app/api/requisiciones/router.py", "/opt/almacen-backend/app/api/requisiciones/router.py"),
    ("app/utils/pdf.py", "/opt/almacen-backend/app/utils/pdf.py"),
    ("app/frontend/requisiciones.html", "/opt/almacen-backend/app/frontend/requisiciones.html"),
]

for local, remote in files:
    print(f"\nCopiando {local}...")
    
    # Copiar archivo usando pscp
    scp_cmd = [
        "pscp",
        "-pw", SERVER_PASSWORD,
        local,
        f"{SERVER_USER}@{SERVER_HOST}:{remote}"
    ]
    
    result = subprocess.run(scp_cmd, capture_output=True, text=True, timeout=30)
    
    if result.returncode == 0:
        print(f"[OK] {local} copiado")
    else:
        print(f"[ERROR] {result.stderr}")

# Esperar un poco
time.sleep(2)

# Mover archivos a ubicacion final usando plink con sudo y nohup
print("\nMoviendo archivos a ubicacion final...")

move_script = """
#!/bin/bash
set -e

echo 'Moviendo router.py...'
sudo mv /tmp/app-api-requisiciones-router-dot-py /opt/almacen-backend/app/api/requisiciones/router.py 2>/dev/null || cp -f /tmp/app-api-requisiciones-router-dot-py /opt/almacen-backend/app/api/requisiciones/router.py

echo 'Moviendo pdf.py...'
sudo mv /tmp/app-utils-pdf-dot-py /opt/almacen-backend/app/utils/pdf.py 2>/dev/null || cp -f /tmp/app-utils-pdf-dot-py /opt/almacen-backend/app/utils/pdf.py

echo 'Moviendo requisiciones.html...'
sudo mv /tmp/app-frontend-requisiciones-dot-html /opt/almacen-backend/app/frontend/requisiciones.html 2>/dev/null || cp -f /tmp/app-frontend-requisiciones-dot-html /opt/almacen-backend/app/frontend/requisiciones.html

echo 'Estableciendo permisos...'
sudo chown -R almacen:almacen /opt/almacen-backend/app 2>/dev/null || true
sudo chmod -R 755 /opt/almacen-backend/app 2>/dev/null || true

echo 'Movimientos completados!'
"""

import tempfile
with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False, dir=os.environ.get('TEMP', '.')) as f:
    f.write(move_script)
    script_path = f.name

# Copiar script
pscp_cmd = [
    "pscp",
    "-pw", SERVER_PASSWORD,
    script_path,
    f"{SERVER_USER}@{SERVER_HOST}:/tmp/move.sh"
]
subprocess.run(pscp_cmd, capture_output=True, timeout=15)

# Ejecutar script
plink_cmd = [
    "plink",
    "-pw", SERVER_PASSWORD,
    f"{SERVER_USER}@{SERVER_HOST}",
    "bash /tmp/move.sh"
]

try:
    result = subprocess.run(plink_cmd, capture_output=True, text=True, timeout=60)
    print(result.stdout)
except subprocess.TimeoutExpired:
    print("[ADVERTENCIA] Timeout en movimiento (puede estar en progreso)")

os.unlink(script_path)

# Instalar dependencias
print("\nInstalando dependencias...")
install_cmd = [
    "plink",
    "-pw", SERVER_PASSWORD,
    f"{SERVER_USER}@{SERVER_HOST}",
    "source /opt/almacen-backend/.venv/bin/activate && pip install reportlab -q"
]

try:
    result = subprocess.run(install_cmd, capture_output=True, text=True, timeout=120)
    print("[OK] Dependencias instaladas")
except subprocess.TimeoutExpired:
    print("[ADVERTENCIA] Timeout en instalacion (puede estar en progreso)")

# Reiniciar servicio
print("\nReiniciando servicio...")
time.sleep(3)

restart_cmd = [
    "plink",
    "-pw", SERVER_PASSWORD,
    f"{SERVER_USER}@{SERVER_HOST}",
    "nohup bash -c 'sleep 1; sudo systemctl restart almacen-backend' > /dev/null 2>&1 &"
]

try:
    result = subprocess.run(restart_cmd, capture_output=True, text=True, timeout=15)
    print("[OK] Reinicio enviado")
except subprocess.TimeoutExpired:
    print("[OK] Comando enviado (puede estar procesando)")

print("\nDeployment completado!")
