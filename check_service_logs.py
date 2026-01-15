#!/usr/bin/env python3
"""Ver logs del servicio para errores de import"""

import paramiko

SERVER = "192.168.180.164"
USER = "administrador"  
PASSWORD = "DHumanos25"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(SERVER, username=USER, password=PASSWORD, allow_agent=False, look_for_keys=False)

# Ver los logs desde el último reinicio
stdin, stdout, stderr = client.exec_command(
    "journalctl -u almacen-backend --since '5 minutes ago' --no-pager | grep -E 'Started|ERROR|Failed|Traceback|ModuleNotFoundError|SyntaxError|router|notificaciones'"
)

output = stdout.read().decode()

print("Logs del servicio (últimos 5 minutos):")
print("=" * 70)
print(output if output else "(sin resultados)")

# Ver si hay errores en general
stdin, stdout, stderr = client.exec_command(
    "journalctl -u almacen-backend --since '5 minutes ago' --no-pager | tail -30"
)

output = stdout.read().decode()

print("\n" + "=" * 70)
print("Últimas 30 líneas de logs:")
print("=" * 70)
print(output)

client.close()
