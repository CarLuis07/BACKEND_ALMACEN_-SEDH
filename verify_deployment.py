#!/usr/bin/env python3
import subprocess
import time
import requests

SERVER_HOST = "192.168.180.164"
SERVER_USER = "administrador"
SERVER_PASSWORD = "DHumanos25"

print("\n" + "=" * 70)
print("VERIFICACION POST-DEPLOYMENT")
print("=" * 70)

# 1. Verificar archivos en servidor
print("\n[1] Verificando archivos en servidor...")
check_files_cmd = [
    "plink",
    "-pw", SERVER_PASSWORD,
    f"{SERVER_USER}@{SERVER_HOST}",
    "ls -lh /opt/almacen-backend/app/api/requisiciones/router.py /opt/almacen-backend/app/utils/pdf.py /opt/almacen-backend/app/frontend/requisiciones.html"
]

try:
    result = subprocess.run(check_files_cmd, capture_output=True, text=True, timeout=10)
    print(result.stdout)
except Exception as e:
    print(f"    Error: {e}")

# 2. Verificar status del servicio
print("\n[2] Estado del servicio...")
status_cmd = [
    "plink",
    "-pw", SERVER_PASSWORD,
    f"{SERVER_USER}@{SERVER_HOST}",
    "systemctl is-active almacen-backend && echo ACTIVO || echo INACTIVO"
]

try:
    result = subprocess.run(status_cmd, capture_output=True, text=True, timeout=10)
    output = result.stdout.strip()
    if "ACTIVO" in output:
        print("    [OK] Servicio esta ACTIVO")
    else:
        print("    [ADVERTENCIA] Servicio no esta activo")
        print(f"    Output: {output}")
except Exception as e:
    print(f"    Error: {e}")

# 3. Verificar que reportlab este instalado
print("\n[3] Verificando dependencias en servidor...")
check_deps_cmd = [
    "plink",
    "-pw", SERVER_PASSWORD,
    f"{SERVER_USER}@{SERVER_HOST}",
    "/opt/almacen-backend/.venv/bin/pip list | grep -i reportlab"
]

try:
    result = subprocess.run(check_deps_cmd, capture_output=True, text=True, timeout=15)
    if result.returncode == 0 and result.stdout.strip():
        print(f"    {result.stdout.strip()}")
    else:
        print("    [ADVERTENCIA] reportlab podria no estar instalado")
        print("    Instalando...")
        install_cmd = [
            "plink",
            "-pw", SERVER_PASSWORD,
            f"{SERVER_USER}@{SERVER_HOST}",
            "source /opt/almacen-backend/.venv/bin/activate && pip install reportlab -q && echo 'Instalado'"
        ]
        result = subprocess.run(install_cmd, capture_output=True, text=True, timeout=30)
        print(result.stdout)
except Exception as e:
    print(f"    Error: {e}")

# 4. Probar endpoint
print("\n[4] Probando endpoint...")
time.sleep(2)
try:
    url = "http://192.168.180.164:8081/requisiciones"
    response = requests.get(url, timeout=5)
    if response.status_code == 200:
        print(f"    [OK] Sitio accesible (HTTP {response.status_code})")
    else:
        print(f"    Status: {response.status_code}")
except Exception as e:
    print(f"    Error: {e}")

# 5. Verificar logs del servicio
print("\n[5] Ultimas lineas del log del servicio...")
log_cmd = [
    "plink",
    "-pw", SERVER_PASSWORD,
    f"{SERVER_USER}@{SERVER_HOST}",
    "journalctl -u almacen-backend -n 10 --no-pager"
]

try:
    result = subprocess.run(log_cmd, capture_output=True, text=True, timeout=10)
    print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
except Exception as e:
    print(f"    Error: {e}")

print("\n" + "=" * 70)
print("VERIFICACION COMPLETADA")
print("=" * 70)
print("\nProximos pasos:")
print("1. Acceder a http://192.168.180.164:8081")
print("2. Login con usuario EmpAlmacen")
print("3. Ir a Requisiciones")
print("4. Buscar una requisicion con estado 'APROBADO'")
print("5. Deberia ver el boton 'Finalizar'")
print("\n")
