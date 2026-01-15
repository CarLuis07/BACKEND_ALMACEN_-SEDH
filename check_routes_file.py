#!/usr/bin/env python3
"""Verificar rutas usando archivo temporal"""

import paramiko

SERVER = "192.168.180.164"
USER = "administrador"  
PASSWORD = "DHumanos25"

# Script de Python a ejecutar en el servidor
check_script = '''import sys
sys.path.insert(0, '/opt/almacen-backend')
from app.main import app

print("=" * 70)
print("RUTAS DE NOTIFICACIONES REGISTRADAS EN FASTAPI")
print("=" * 70)

notif_routes = []
for route in app.routes:
    path = str(route.path)
    if 'notificaciones' in path:
        methods = route.methods if hasattr(route, 'methods') else []
        notif_routes.append((path, methods))
        print(f"{path}")
        for method in (methods if methods else []):
            print(f"  - {method}")

print(f"\\nTotal rutas: {len(notif_routes)}")
if len(notif_routes) == 4:
    print("✓ TODAS LAS 4 RUTAS ESTÁN REGISTRADAS")
elif len(notif_routes) == 0:
    print("✗ NO HAY RUTAS DE NOTIFICACIONES")
else:
    print(f"✗ SOLO {len(notif_routes)}/4 RUTAS REGISTRADAS")
'''

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    client.connect(SERVER, username=USER, password=PASSWORD, allow_agent=False, look_for_keys=False)
    
    # Escribir script en archivo temporal
    stdin, stdout, stderr = client.exec_command(
        "cat > /tmp/check_routes.py << 'EOFSCRIPT'\n" + check_script + "\nEOFSCRIPT"
    )
    stdout.channel.recv_exit_status()
    
    # Ejecutar script
    stdin, stdout, stderr = client.exec_command(
        "/opt/almacen-backend/venv/bin/python3 /tmp/check_routes.py"
    )
    
    output = stdout.read().decode()
    error = stderr.read().decode()
    
    print(output)
    
    if error:
        print("\nErrores:")
        print(error[:500])
    
finally:
    client.close()
