#!/usr/bin/env python3
import subprocess
import os
import time

SERVER_HOST = "192.168.180.164"
SERVER_USER = "administrador"
SERVER_PASSWORD = "DHumanos25"

print("\n" + "=" * 70)
print("DEPLOYMENT FINAL - COPIA A /tmp Y MOVIMIENTO CON SUDO")
print("=" * 70)

files = [
    ("app/api/requisiciones/router.py", "/tmp/router-py"),
    ("app/utils/pdf.py", "/tmp/pdf-py"),
    ("app/frontend/requisiciones.html", "/tmp/requisiciones-html"),
]

print("\n[1] Copiando archivos a /tmp del servidor...")
for local, remote_tmp in files:
    print(f"\n    {local} -> {remote_tmp}")
    
    scp_cmd = [
        "pscp",
        "-pw", SERVER_PASSWORD,
        local,
        f"{SERVER_USER}@{SERVER_HOST}:{remote_tmp}"
    ]
    
    result = subprocess.run(scp_cmd, capture_output=True, text=True, timeout=30)
    
    if result.returncode == 0:
        print(f"    [OK]")
    else:
        print(f"    [ERROR] {result.stderr}")

time.sleep(2)

print("\n[2] Moviendo archivos a ubicacion final con sudo...")

# Script para mover desde /tmp a /opt con sudo
move_script = """#!/bin/bash
set -e

echo 'Creando directorios...'
sudo mkdir -p /opt/almacen-backend/app/api/requisiciones
sudo mkdir -p /opt/almacen-backend/app/utils
sudo mkdir -p /opt/almacen-backend/app/frontend

echo 'Moviendo router.py...'
sudo cp /tmp/router-py /opt/almacen-backend/app/api/requisiciones/router.py
sudo chown almacen:almacen /opt/almacen-backend/app/api/requisiciones/router.py

echo 'Moviendo pdf.py...'
sudo cp /tmp/pdf-py /opt/almacen-backend/app/utils/pdf.py
sudo chown almacen:almacen /opt/almacen-backend/app/utils/pdf.py

echo 'Moviendo requisiciones.html...'
sudo cp /tmp/requisiciones-html /opt/almacen-backend/app/frontend/requisiciones.html
sudo chown almacen:almacen /opt/almacen-backend/app/frontend/requisiciones.html

echo '[OK] Todos los archivos movidos!'
"""

import tempfile
with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
    f.write(move_script)
    script_path = f.name

# Copiar script a servidor
print("\n    Copiando script de movimiento...")
pscp_cmd = [
    "pscp",
    "-pw", SERVER_PASSWORD,
    script_path,
    f"{SERVER_USER}@{SERVER_HOST}:/tmp/move.sh"
]
subprocess.run(pscp_cmd, capture_output=True, timeout=15)

# Ejecutar script
print("    Ejecutando movimiento...")
plink_cmd = [
    "plink",
    "-pw", SERVER_PASSWORD,
    f"{SERVER_USER}@{SERVER_HOST}",
    "bash /tmp/move.sh"
]

try:
    result = subprocess.run(plink_cmd, capture_output=True, text=True, timeout=120)
    print(result.stdout)
    if result.stderr and "Access granted" not in result.stderr:
        print("STDERR:", result.stderr)
except subprocess.TimeoutExpired:
    print("    [ADVERTENCIA] Timeout en movimiento")

os.unlink(script_path)

time.sleep(2)

print("\n[3] Instalando dependencias...")
install_cmd = [
    "plink",
    "-pw", SERVER_PASSWORD,
    f"{SERVER_USER}@{SERVER_HOST}",
    "source /opt/almacen-backend/.venv/bin/activate && pip install reportlab -q && echo 'OK'"
]

try:
    result = subprocess.run(install_cmd, capture_output=True, text=True, timeout=180)
    if "OK" in result.stdout or "Requirement already" in result.stdout:
        print("    [OK] reportlab instalado/verificado")
    else:
        print("    Output:", result.stdout[:200])
except subprocess.TimeoutExpired:
    print("    [ADVERTENCIA] Timeout en instalacion")

time.sleep(3)

print("\n[4] Reiniciando servicio...")
restart_cmd = [
    "plink",
    "-pw", SERVER_PASSWORD,
    f"{SERVER_USER}@{SERVER_HOST}",
    "sudo systemctl restart almacen-backend && sleep 2 && systemctl is-active almacen-backend"
]

try:
    result = subprocess.run(restart_cmd, capture_output=True, text=True, timeout=30)
    output = result.stdout.strip()
    if "active" in output.lower():
        print("    [OK] Servicio activo")
    else:
        print("    Status:", output)
except subprocess.TimeoutExpired:
    print("    [ADVERTENCIA] Timeout en restart (servicio puede estar reiniciando)")

print("\n" + "=" * 70)
print("DEPLOYMENT COMPLETADO")
print("=" * 70)

time.sleep(3)

print("\n[5] Verificando endpoint...")
try:
    import requests
    response = requests.get("http://192.168.180.164:8081/requisiciones", timeout=5)
    print(f"    HTTP {response.status_code} - Sitio accesible")
except Exception as e:
    print(f"    Error: {e}")

print("\n")
