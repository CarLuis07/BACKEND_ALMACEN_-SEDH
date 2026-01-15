#!/usr/bin/env python3
"""Verificar rutas usando el endpoint openapi.json"""

import paramiko
import json

SERVER = "192.168.180.164"
USER = "administrador"  
PASSWORD = "DHumanos25"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(SERVER, username=USER, password=PASSWORD, allow_agent=False, look_for_keys=False)

# Obtener el schema OpenAPI que lista todas las rutas
stdin, stdout, stderr = client.exec_command(
    'curl -s http://127.0.0.1:8081/openapi.json'
)

output = stdout.read().decode()

try:
    openapi = json.loads(output)
    
    print("=" * 70)
    print("RUTAS DE NOTIFICACIONES EN OPENAPI")
    print("=" * 70)
    
    paths = openapi.get("paths", {})
    notif_paths = []
    
    for path, methods in paths.items():
        if 'notificaciones' in path:
            notif_paths.append(path)
            print(f"\n{path}")
            for method, details in methods.items():
                if method.upper() in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                    summary = details.get("summary", "(sin resumen)")
                    print(f"  {method.upper()}: {summary}")
    
    print(f"\n{'=' * 70}")
    print(f"Total rutas con 'notificaciones': {len(notif_paths)}")
    
    if len(notif_paths) >= 4:
        print("✓ ¡TODAS LAS RUTAS ESTÁN REGISTRADAS!")
    elif len(notif_paths) == 0:
        print("✗ NO SE ENCONTRARON RUTAS DE NOTIFICACIONES")
    else:
        print(f"✗ Solo {len(notif_paths)}/4 rutas presentes")
    
except json.JSONDecodeError as e:
    print(f"Error decodificando JSON: {e}")
    print(f"Respuesta: {output[:500]}")

client.close()
