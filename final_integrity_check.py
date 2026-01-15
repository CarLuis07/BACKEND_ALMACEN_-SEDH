#!/usr/bin/env python3
"""Confirmar integridad 100% del archivo"""

import paramiko
import hashlib

SERVER = "192.168.180.164"
USER = "administrador"  
PASSWORD = "DHumanos25"

# Calcular hash local
with open(r"c:\Users\Programador1\almacen-backend\app\api\requisiciones\router.py", "rb") as f:
    local_content = f.read()
    local_hash = hashlib.md5(local_content).hexdigest()
    local_lines = local_content.decode('utf-8').split('\n')

print("=" * 70)
print("COMPARACIÓN LOCAL vs REMOTO")
print("=" * 70)
print(f"\nArchivo local:")
print(f"  Líneas: {len(local_lines)}")
print(f"  Hash MD5: {local_hash}")
print(f"  Tamaño: {len(local_content)} bytes")

# Líneas específicas con decoradores
decorator_lines = [2810, 2867, 2901, 2925]
print(f"\nDecoradores en archivo local:")
for line_num in decorator_lines:
    if line_num < len(local_lines):
        print(f"  {line_num}: {local_lines[line_num-1][:80]}")

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(SERVER, username=USER, password=PASSWORD, allow_agent=False, look_for_keys=False)

# Hash remoto
stdin, stdout, stderr = client.exec_command(
    "md5sum /opt/almacen-backend/app/api/requisiciones/router.py"
)
remote_hash_output = stdout.read().decode().strip()
remote_hash = remote_hash_output.split()[0] if remote_hash_output else "N/A"

# Líneas remotas
stdin, stdout, stderr = client.exec_command(
    "wc -l /opt/almacen-backend/app/api/requisiciones/router.py"
)
remote_lines = stdout.read().decode().strip().split()[0]

# Tamaño
stdin, stdout, stderr = client.exec_command(
    "stat -c%s /opt/almacen-backend/app/api/requisiciones/router.py"
)
remote_size = stdout.read().decode().strip()

print(f"\n{'-' * 70}")
print(f"Archivo remoto:")
print(f"  Líneas: {remote_lines}")
print(f"  Hash MD5: {remote_hash}")
print(f"  Tamaño: {remote_size} bytes")

# Líneas específicas remotas
print(f"\nDecoradores en archivo remoto:")
for line_num in decorator_lines:
    stdin, stdout, stderr = client.exec_command(
        f"sed -n '{line_num}p' /opt/almacen-backend/app/api/requisiciones/router.py"
    )
    line = stdout.read().decode().strip()
    print(f"  {line_num}: {line[:80]}")

print(f"\n{'=' * 70}")
if local_hash == remote_hash:
    print("✓ LOS ARCHIVOS SON IDÉNTICOS")
else:
    print("✗ LOS ARCHIVOS SON DIFERENTES")
    print("\nEsto indica que la copia no fue exitosa o se modificó el archivo")

# Verificar WorkingDirectory del servicio
stdin, stdout, stderr = client.exec_command(
    "systemctl show almacen-backend | grep WorkingDirectory"
)
wd = stdout.read().decode().strip()
print(f"\n{wd}")

# Verificar que no hay otro router.py que se esté usando
stdin, stdout, stderr = client.exec_command(
    "find /opt/almacen-backend -name 'router.py' -path '*/requisiciones/*'"
)
router_files = stdout.read().decode().strip()
print(f"\nArchivos router.py encontrados:")
print(router_files)

client.close()
