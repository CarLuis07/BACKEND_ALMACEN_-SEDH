#!/usr/bin/env python3
"""Kill forzado del proceso y reinicio real"""

import paramiko
import time

SERVER = "192.168.180.164"
USER = "administrador"  
PASSWORD = "DHumanos25"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(SERVER, username=USER, password=PASSWORD, allow_agent=False, look_for_keys=False)

# Ver PID actual
stdin, stdout, stderr = client.exec_command(
    "pgrep -f 'uvicorn app.main:app'"
)
old_pid = stdout.read().decode().strip()
print(f"PID actual del servicio: {old_pid}")

# Kill forzado
if old_pid:
    print(f"\nMatando proceso {old_pid} con SIGKILL...")
    stdin, stdout, stderr = client.exec_command(
        f"kill -9 {old_pid}"
    )
    stdout.channel.recv_exit_status()
    print("✓ Proceso eliminado")
    time.sleep(2)

# Eliminar cache
print("\nEliminando todo el cache de Python...")
stdin, stdout, stderr = client.exec_command(
    "find /opt/almacen-backend/app -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true"
)
stdout.channel.recv_exit_status()

stdin, stdout, stderr = client.exec_command(
    "find /opt/almacen-backend/app -name '*.pyc' -delete 2>/dev/null || true"
)
stdout.channel.recv_exit_status()
print("✓ Cache eliminado")

time.sleep(1)

# Iniciar servicio limpio
print("\nIniciando servicio fresco...")
stdin, stdout, stderr = client.exec_command(
    "systemctl start almacen-backend"
)
stdout.channel.recv_exit_status()

time.sleep(5)

# Verificar nuevo PID
stdin, stdout, stderr = client.exec_command(
    "pgrep -f 'uvicorn app.main:app'"
)
new_pid = stdout.read().decode().strip()
print(f"Nuevo PID: {new_pid}")

if new_pid != old_pid:
    print("✓ Proceso realmente se reinició")
else:
    print("✗ WARNING: PID no cambió")

# Verificar estado
stdin, stdout, stderr = client.exec_command(
    "systemctl is-active almacen-backend"
)
status = stdout.read().decode().strip()
print(f"Estado: {status}")

time.sleep(2)

# Probar endpoint
print("\nProbando endpoint...")
stdin, stdout, stderr = client.exec_command(
    'curl -s -w "\\n%{http_code}" http://127.0.0.1:8081/api/v1/requisiciones/notificaciones -H "Authorization: Bearer test"'
)
response = stdout.read().decode()
lines = response.split('\n')
if lines:
    http_code = lines[-1]
    body = '\n'.join(lines[:-1])
    
    print(f"HTTP Code: {http_code}")
    print(f"Body: {body[:150]}")
    
    if http_code in ["200", "401"]:
        print("\n" + "=" * 70)
        print("✓✓✓ ¡ENDPOINT FUNCIONANDO! ✓✓✓")
        print("=" * 70)
    else:
        print(f"\n✗ Aún error HTTP {http_code}")

# Verificar OpenAPI
print("\nVerificando OpenAPI...")
stdin, stdout, stderr = client.exec_command(
    'curl -s http://127.0.0.1:8081/openapi.json | grep -c "notificaciones"'
)
count = stdout.read().decode().strip()
print(f"Menciones de 'notificaciones' en OpenAPI: {count}")

if int(count) > 0:
    print("✓ Rutas de notificaciones ahora están en OpenAPI")

client.close()
