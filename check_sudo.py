#!/usr/bin/env python3
"""Verificar permisos sudo"""

import paramiko

SERVER = "192.168.180.164"
USER = "administrador"  
PASSWORD = "DHumanos25"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(SERVER, username=USER, password=PASSWORD, allow_agent=False, look_for_keys=False)

# Probar sudo
stdin, stdout, stderr = client.exec_command(
    "sudo -n whoami 2>&1"
)
output = stdout.read().decode().strip()
error = stderr.read().decode().strip()

print("Resultado de sudo:")
print(output)
if error:
    print(f"Error: {error}")

# Ver el servicio del systemd
stdin, stdout, stderr = client.exec_command(
    "systemctl status almacen-backend | head -20"
)
output = stdout.read().decode()

print("\nEstado del servicio:")
print(output)

# Ver el process tree
stdin, stdout, stderr = client.exec_command(
    "ps auxf | grep -A3 almacen | grep -v grep"
)
output = stdout.read().decode()

print("\nProcess tree:")
print(output)

client.close()
