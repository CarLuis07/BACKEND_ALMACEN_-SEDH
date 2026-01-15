#!/usr/bin/env python3
"""Verificar que se eliminó el cache"""

import paramiko

SERVER = "192.168.180.164"
USER = "administrador"  
PASSWORD = "DHumanos25"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(SERVER, username=USER, password=PASSWORD, allow_agent=False, look_for_keys=False)

# Verificar timestamp del router.py
stdin, stdout, stderr = client.exec_command(
    "ls -lh /opt/almacen-backend/app/api/requisiciones/router.py"
)
print("Timestamp de router.py:")
print(stdout.read().decode())

# Verificar si hay __pycache__
stdin, stdout, stderr = client.exec_command(
    "ls -lh /opt/almacen-backend/app/api/requisiciones/__pycache__/router*.pyc 2>&1 | head -5"
)
print("\nCache files:")
print(stdout.read().decode())

# Ver uptime del proceso
stdin, stdout, stderr = client.exec_command(
    "ps -p $(pgrep -f 'almacen-backend') -o pid,etime,cmd"
)
print("\nProceso del servicio:")
print(stdout.read().decode())

# Verificar logs del reinicio más reciente
stdin, stdout, stderr = client.exec_command(
    "journalctl -u almacen-backend | grep -E 'Started|Stopping' | tail -5"
)
print("\nReinicio más reciente:")
print(stdout.read().decode())

client.close()
