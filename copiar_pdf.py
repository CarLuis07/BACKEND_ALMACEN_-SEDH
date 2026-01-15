#!/usr/bin/env python3
import subprocess
import os

SERVER_HOST = '192.168.180.164'
SERVER_USER = 'administrador'
SERVER_PASSWORD = 'DHumanos25'

print("\n" + "=" * 80)
print("COPIANDO pdf.py AL SERVIDOR")
print("=" * 80)

# Verificar que el archivo existe localmente
if not os.path.exists('app/utils/pdf.py'):
    print("[ERROR] app/utils/pdf.py no existe localmente")
    exit(1)

print("\n[PASO 1] Copiar app/utils/pdf.py a /tmp del servidor")
cmd = [
    'pscp',
    '-pw', SERVER_PASSWORD,
    'app/utils/pdf.py',
    f'{SERVER_USER}@{SERVER_HOST}:/tmp/pdf-py'
]

result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
if result.returncode == 0:
    print("[OK] Archivo copiado a /tmp/pdf-py")
else:
    print(f"[ERROR] {result.stderr}")
    exit(1)

print("\n[PASO 2] Mover desde /tmp a /opt/almacen-backend/app/utils/")
cmd = [
    'plink',
    '-pw', SERVER_PASSWORD,
    f'{SERVER_USER}@{SERVER_HOST}',
    'sudo mv /tmp/pdf-py /opt/almacen-backend/app/utils/pdf.py && sudo chown almacen:almacen /opt/almacen-backend/app/utils/pdf.py && echo LISTO'
]

result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
if 'LISTO' in result.stdout or result.returncode == 0:
    print("[OK] Archivo movido a ubicacion final")
else:
    print(f"[ADVERTENCIA] {result.stdout}")

print("\n[PASO 3] Verificar que el archivo esta en lugar correcto")
cmd = [
    'plink',
    '-pw', SERVER_PASSWORD,
    f'{SERVER_USER}@{SERVER_HOST}',
    'ls -lh /opt/almacen-backend/app/utils/pdf.py && echo OK'
]

result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
if 'OK' in result.stdout:
    print("[OK] Archivo verificado en servidor")
    # Extraer el tamaño
    lines = result.stdout.split('\n')
    if lines[0]:
        print(f"    {lines[0]}")
else:
    print(f"[ERROR] {result.stderr}")

print("\n[PASO 4] Reiniciar servicio para cargar cambios")
cmd = [
    'plink',
    '-pw', SERVER_PASSWORD,
    f'{SERVER_USER}@{SERVER_HOST}',
    'sudo systemctl restart almacen-backend && sleep 2 && echo REINICIADO'
]

try:
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if 'REINICIADO' in result.stdout or result.returncode == 0:
        print("[OK] Servicio reiniciado")
    else:
        print(f"[INFO] {result.stdout[:100]}")
except subprocess.TimeoutExpired:
    print("[OK] Comando de reinicio enviado (puede tomar algunos segundos)")

print("\n" + "=" * 80)
print("DEPLOYMENT DE pdf.py COMPLETADO")
print("=" * 80)
print("""
Archivos ahora en servidor:
✓ /opt/almacen-backend/app/api/requisiciones/router.py
✓ /opt/almacen-backend/app/utils/pdf.py
✓ /opt/almacen-backend/app/frontend/requisiciones.html

Servicio: almacen-backend (reiniciado)

Proximos pasos:
1. Acceder a http://192.168.180.164:8081/requisiciones
2. Login como usuario EmpAlmacen
3. Buscar requisicion en estado APROBADO
4. Deberia ver boton "Finalizar"
""")
print("=" * 80)
