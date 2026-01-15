#!/usr/bin/env python3
"""Verificar si hay errores silenciosos en el import"""

import paramiko

SERVER = "192.168.180.164"
USER = "administrador"  
PASSWORD = "DHumanos25"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(SERVER, username=USER, password=PASSWORD, allow_agent=False, look_for_keys=False)

# Ver los logs completos del inicio del servicio
stdin, stdout, stderr = client.exec_command(
    "journalctl -u almacen-backend --since '10 minutes ago' --no-pager | grep -A5 -B5 'Started server\\|Application startup'"
)

output = stdout.read().decode()
print("Logs de inicio del servidor:")
print("=" * 70)
print(output if output else "(sin resultados)")

# Buscar warnings o errores
stdin, stdout, stderr = client.exec_command(
    "journalctl -u almacen-backend --since '10 minutes ago' --no-pager | grep -iE 'warning|error|exception|traceback|failed' | head -20"
)

output = stdout.read().decode()
print("\n" + "=" * 70)
print("Warnings/Errores:")
print("=" * 70)
print(output if output else "(ninguno encontrado)")

# Ver TODAS las rutas registradas
stdin, stdout, stderr = client.exec_command(
    "curl -s http://127.0.0.1:8081/openapi.json | grep -o '\"*/api/v1/requisiciones[^\"]*\"' | sort -u | tail -20"
)

output = stdout.read().decode()
print("\n" + "=" * 70)
print("Rutas de requisiciones en OpenAPI:")
print("=" * 70)
print(output if output else "(ninguna)")

client.close()
