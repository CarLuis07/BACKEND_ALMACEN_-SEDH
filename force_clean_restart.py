#!/usr/bin/env python3
"""Reinicio forzado con eliminación de cache"""

import paramiko
import time

SERVER = "192.168.180.164"
USER = "administrador"  
PASSWORD = "DHumanos25"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(SERVER, username=USER, password=PASSWORD, allow_agent=False, look_for_keys=False)

commands = [
    ("Deteniendo servicio...", "systemctl stop almacen-backend"),
    ("Esperando 2 segundos...", "sleep 2"),
    ("Eliminando cache de requisiciones...", "rm -f /opt/almacen-backend/app/api/requisiciones/__pycache__/router*.pyc"),
    ("Eliminando cache de main...", "rm -f /opt/almacen-backend/app/__pycache__/*.pyc"),
    ("Eliminando cache de api...", "rm -f /opt/almacen-backend/app/api/__pycache__/*.pyc"),
    ("Iniciando servicio...", "systemctl start almacen-backend"),
    ("Esperando 4 segundos...", "sleep 4"),
    ("Verificando estado...", "systemctl is-active almacen-backend"),
]

for desc, cmd in commands:
    print(desc)
    stdin, stdout, stderr = client.exec_command(cmd)
    stdout.channel.recv_exit_status()
    if "sleep" not in cmd:
        output = stdout.read().decode().strip()
        if output:
            print(f"  {output}")

# Verificar que realmente se eliminaron los caches
stdin, stdout, stderr = client.exec_command(
    "ls -lh /opt/almacen-backend/app/api/requisiciones/__pycache__/router*.pyc 2>&1"
)
print("\nCache después de reinicio:")
print(stdout.read().decode())

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
        print("✓ ¡ENDPOINT FUNCIONANDO!")
        print("=" * 70)
    else:
        print("\n✗ Endpoint aún retorna error")

# Ver OpenAPI
print("\nVerificando OpenAPI...")
stdin, stdout, stderr = client.exec_command(
    'curl -s http://127.0.0.1:8081/openapi.json | grep -o "\\"notificaciones[^"]*\\"" | sort -u'
)
notif_routes = stdout.read().decode().strip()
if notif_routes:
    print("Rutas encontradas:")
    print(notif_routes)
else:
    print("(ninguna ruta de notificaciones encontrada)")

client.close()
