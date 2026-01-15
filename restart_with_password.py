#!/usr/bin/env python3
"""Reinicio con contraseña de sudo"""

import paramiko
import time

SERVER = "192.168.180.164"
USER = "administrador"  
PASSWORD = "DHumanos25"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(SERVER, username=USER, password=PASSWORD, allow_agent=False, look_for_keys=False)

print("=" * 70)
print("REINICIO COMPLETO DEL SERVICIO")
print("=" * 70)

# Usar echo para pasar la contraseña a sudo
commands = [
    f"echo {PASSWORD} | sudo -S systemctl stop almacen-backend",
    "sleep 3",
    f"echo {PASSWORD} | sudo -S find /opt/almacen-backend/app -name '__pycache__' -type d -exec rm -rf {{}} + 2>/dev/null || true",
    f"echo {PASSWORD} | sudo -S systemctl start almacen-backend",
    "sleep 5",
]

for cmd in commands:
    if "sleep" in cmd:
        time.sleep(int(cmd.split()[1]))
        print(f"Esperando {cmd.split()[1]} segundos...")
    else:
        print(f"\nEjecutando: {cmd.split('|')[-1].strip()[:50]}...")
        stdin, stdout, stderr = client.exec_command(cmd)
        stdout.channel.recv_exit_status()
        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()
        
        if output and "password" not in output.lower():
            print(f"  {output}")
        if error and "password" not in error.lower() and "sudo" not in error.lower():
            print(f"  Error: {error[:200]}")

# Verificar estado
stdin, stdout, stderr = client.exec_command("systemctl is-active almacen-backend")
status = stdout.read().decode().strip()
print(f"\n✓ Estado del servicio: {status}")

# Verificar PID cambió
stdin, stdout, stderr = client.exec_command("pgrep -f 'uvicorn app.main:app'")
new_pid = stdout.read().decode().strip()
print(f"✓ Nuevo PID: {new_pid}")

time.sleep(3)

# Probar endpoint
print("\n" + "=" * 70)
print("PROBANDO ENDPOINT")
print("=" * 70)

stdin, stdout, stderr = client.exec_command(
    'curl -s -w "\\n%{http_code}" http://127.0.0.1:8081/api/v1/requisiciones/notificaciones -H "Authorization: Bearer test"'
)
response = stdout.read().decode()
lines = response.split('\n')
http_code = lines[-1] if lines else "??"
body = '\n'.join(lines[:-1]) if len(lines) > 1 else ""

print(f"\nHTTP Code: {http_code}")
if body:
    print(f"Body: {body[:200]}")

if http_code in ["200", "401"]:
    print("\n" + "=" * 70)
    print("✓✓✓ ¡ÉXITO! ENDPOINT FUNCIONANDO ✓✓✓")
    print("=" * 70)
    print("\nLas notificaciones ahora deberían funcionar en el dashboard.")
    print("Abre: http://192.168.180.164:8081/dashboard")
elif http_code == "404":
    print("\n✗ Aún retorna 404")
    print("Verificando OpenAPI...")
    
    stdin, stdout, stderr = client.exec_command(
        'curl -s http://127.0.0.1:8081/openapi.json | grep -o "\\"notificaciones\\"" | wc -l'
    )
    count = stdout.read().decode().strip()
    print(f"Menciones en OpenAPI: {count}")
else:
    print(f"\n✗ Error HTTP {http_code}")

client.close()
