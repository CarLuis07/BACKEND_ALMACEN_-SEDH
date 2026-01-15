#!/usr/bin/env python3
"""Verificar rutas de forma simple"""

import paramiko
import time

SERVER = "192.168.180.164"
USER = "administrador"  
PASSWORD = "DHumanos25"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(SERVER, username=USER, password=PASSWORD, allow_agent=False, look_for_keys=False)

# Script simple sin variables complejas
script = '''
import sys
sys.path.insert(0, '/opt/almacen-backend')
from app.main import app

print("Checking routes...")
count = 0
for route in app.routes:
    if 'notificaciones' in str(route.path):
        print(route.path)
        count = count + 1

print("Total:" + str(count))
'''

stdin, stdout, stderr = client.exec_command(
    "/opt/almacen-backend/venv/bin/python3 -c '" + script.replace("'", "\\'") + "'"
)

output = stdout.read().decode()
error = stderr.read().decode()

print("Resultado:")
print(output)

if error:
    print("Errores:")
    print(error[:500])

client.close()
