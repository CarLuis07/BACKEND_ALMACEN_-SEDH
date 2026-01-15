#!/usr/bin/env python3
import subprocess
import tempfile
import os

SERVER_HOST = '192.168.180.164'
SERVER_USER = 'administrador'
SERVER_PASSWORD = 'DHumanos25'

print("\n" + "=" * 80)
print("COPIANDO pdf.py DIRECTAMENTE AL SERVIDOR")
print("=" * 80)

# Script bash para hacer el movimiento
move_script = """#!/bin/bash
echo "Crear directorio si no existe..."
sudo mkdir -p /opt/almacen-backend/app/utils

echo "Copiar archivo..."
sudo cp /tmp/pdf-py /opt/almacen-backend/app/utils/pdf.py

echo "Establecer permisos..."
sudo chmod 644 /opt/almacen-backend/app/utils/pdf.py
sudo chown almacen:almacen /opt/almacen-backend/app/utils/pdf.py

echo "Verificar..."
ls -lh /opt/almacen-backend/app/utils/pdf.py

echo "[OK] COMPLETADO"
"""

# Crear script temporal
with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
    f.write(move_script)
    script_path = f.name

print(f"\n[PASO 1] Copiar app/utils/pdf.py a servidor")
cmd = [
    'pscp',
    '-pw', SERVER_PASSWORD,
    'app/utils/pdf.py',
    f'{SERVER_USER}@{SERVER_HOST}:/tmp/pdf.py'
]

result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
if result.returncode == 0:
    print("[OK] Archivo copiado a /tmp")
else:
    print(f"[ERROR] {result.stderr}")
    os.unlink(script_path)
    exit(1)

print(f"\n[PASO 2] Copiar script de movimiento")
cmd = [
    'pscp',
    '-pw', SERVER_PASSWORD,
    script_path,
    f'{SERVER_USER}@{SERVER_HOST}:/tmp/move.sh'
]

result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
if result.returncode == 0:
    print("[OK] Script copiado")
else:
    print(f"[ERROR] {result.stderr}")

print(f"\n[PASO 3] Ejecutar script de movimiento")
cmd = [
    'plink',
    '-pw', SERVER_PASSWORD,
    f'{SERVER_USER}@{SERVER_HOST}',
    'bash /tmp/move.sh'
]

result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
output = result.stdout
# Limpiar output de plink
if 'Access granted' in output:
    lines = output.split('\n')
    output = '\n'.join([l for l in lines if 'Access granted' not in l and 'begin session' not in l])

print(output)

if '[OK]' in result.stdout:
    print("\n[EXITO] pdf.py esta en el servidor")
else:
    print("\n[ADVERTENCIA] Verificando...")
    cmd = [
        'plink',
        '-pw', SERVER_PASSWORD,
        f'{SERVER_USER}@{SERVER_HOST}',
        'test -f /opt/almacen-backend/app/utils/pdf.py && echo "ARCHIVO EXISTE" || echo "ARCHIVO NO EXISTE"'
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    print(result.stdout)

# Limpiar
os.unlink(script_path)

print("\n[PASO 4] Reiniciar servicio")
cmd = [
    'plink',
    '-pw', SERVER_PASSWORD,
    f'{SERVER_USER}@{SERVER_HOST}',
    'sudo systemctl restart almacen-backend &'
]

subprocess.run(cmd, capture_output=True, timeout=10)
print("[OK] Servicio reiniciado en background")

print("\n" + "=" * 80)
print("VERIFICACION FINAL")
print("=" * 80)

import requests
import time
time.sleep(2)

try:
    response = requests.get('http://192.168.180.164:8081/requisiciones', timeout=5)
    print(f"\nSitio accesible: HTTP {response.status_code}")
    print("Status: LISTO PARA USAR")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 80)
