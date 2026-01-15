#!/usr/bin/env python3
"""Verificar si FastAPI realmente está registrando las rutas"""

import paramiko

SERVER = "192.168.180.164"
USER = "administrador"  
PASSWORD = "DHumanos25"

def check_routes():
    """Verifica que FastAPI registró las rutas"""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(SERVER, username=USER, password=PASSWORD, allow_agent=False, look_for_keys=False)
        
        # Ejecutar Python para listar rutas
        cmd = '''python3 << 'EOF'
import sys
sys.path.insert(0, '/opt/almacen-backend')

try:
    from app.main import app
    
    print("Rutas registradas en FastAPI:")
    print("=" * 70)
    
    notif_routes = []
    other_routes = 0
    
    for route in app.routes:
        path = str(route.path)
        methods = str(route.methods) if hasattr(route, 'methods') else "N/A"
        
        if 'notificaciones' in path:
            print(f"✓ {path} - {methods}")
            notif_routes.append(path)
        elif 'requisiciones' in path and 'notificaciones' not in path:
            other_routes += 1
    
    print(f"\\nTotal rutas de notificaciones: {len(notif_routes)}")
    print(f"Total otras rutas de requisiciones: {other_routes}")
    
    if len(notif_routes) == 0:
        print("\\n✗ ¡NO HAY RUTAS DE NOTIFICACIONES REGISTRADAS!")
    elif len(notif_routes) < 4:
        print(f"\\n✗ Solo {len(notif_routes)}/4 rutas registradas")
    else:
        print("\\n✓ Todas las 4 rutas están registradas")
        
except Exception as e:
    import traceback
    print(f"Error: {e}")
    traceback.print_exc()
EOF
'''
        
        stdin, stdout, stderr = client.exec_command(cmd)
        output = stdout.read().decode()
        error = stderr.read().decode()
        
        print(output)
        if error:
            print(f"Errores:\n{error}")
        
    finally:
        client.close()

if __name__ == "__main__":
    check_routes()
