#!/usr/bin/env python3
"""Kill con sudo"""

import paramiko
import time

SERVER = "192.168.180.164"
USER = "administrador"  
PASSWORD = "DHumanos25"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(SERVER, username=USER, password=PASSWORD, allow_agent=False, look_for_keys=False)

print("Reinicio COMPLETO del servicio con sudo...")

# Stop con systemctl (que usa sudo internamente)
stdin, stdout, stderr = client.exec_command(
    "sudo systemctl stop almacen-backend"
)
stdout.channel.recv_exit_status()
print("✓ Servicio detenido")

time.sleep(3)

# Verificar que realmente se detuvo
stdin, stdout, stderr = client.exec_command(
    "pgrep -f 'uvicorn app.main:app'"
)
pid = stdout.read().decode().strip()
if pid:
    print(f"⚠ Proceso {pid} aún corriendo, forzando kill...")
    stdin, stdout, stderr = client.exec_command(
        f"sudo kill -9 {pid}"
    )
    stdout.channel.recv_exit_status()
    time.sleep(2)
else:
    print("✓ No hay procesos corriendo")

# Limpiar cache
print("\nLimpiando cache...")
stdin, stdout, stderr = client.exec_command(
    "sudo find /opt/almacen-backend/app -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true"
)
stdout.channel.recv_exit_status()
print("✓ Cache limpiado")

time.sleep(1)

# Iniciar
print("\nIniciando servicio...")
stdin, stdout, stderr = client.exec_command(
    "sudo systemctl start almacen-backend"
)
stdout.channel.recv_exit_status()

time.sleep(5)

# Verificar
stdin, stdout, stderr = client.exec_command(
    "systemctl is-active almacen-backend"
)
status = stdout.read().decode().strip()
print(f"Estado: {status}")

# Nuevo PID
stdin, stdout, stderr = client.exec_command(
    "pgrep -f 'uvicorn app.main:app'"
)
new_pid = stdout.read().decode().strip()
print(f"Nuevo PID: {new_pid}")

time.sleep(2)

# Probar
print("\nProbando endpoint...")
stdin, stdout, stderr = client.exec_command(
    'curl -s -w "\\n%{http_code}" http://127.0.0.1:8081/api/v1/requisiciones/notificaciones -H "Authorization: Bearer test"'
)
response = stdout.read().decode()
lines = response.split('\n')
http_code = lines[-1] if lines else "??"
body = '\n'.join(lines[:-1]) if len(lines) > 1 else ""

print(f"HTTP Code: {http_code}")
print(f"Body: {body[:150]}")

if http_code in ["200", "401"]:
    print("\n" + "=" * 70)
    print("✓✓✓ ¡ÉXITO! ENDPOINT FUNCIONANDO ✓✓✓")
    print("=" * 70)
else:
    print(f"\n✗ HTTP {http_code}")

client.close()
