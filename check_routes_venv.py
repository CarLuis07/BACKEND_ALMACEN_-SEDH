#!/usr/bin/env python3
"""Verificar rutas usando el venv correcto del servicio"""

import paramiko

SERVER = "192.168.180.164"
USER = "administrador"  
PASSWORD = "DHumanos25"

def check_routes_with_correct_venv():
    """Verifica rutas usando el venv del servicio"""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(SERVER, username=USER, password=PASSWORD, allow_agent=False, look_for_keys=False)
        
        # Ejecutar con el venv correcto
        python_exe = "/opt/almacen-backend/venv/bin/python3"
        
        cmd = f'''{python_exe} << 'ENDPYTHON'
import sys
sys.path.insert(0, '/opt/almacen-backend')

try:
    from app.main import app
    
    print("Rutas de notificaciones en FastAPI:")
    notif_routes = []
    for route in app.routes:
        path_str = str(route.path)
        if 'notificaciones' in path_str:
            methods = route.methods if hasattr(route, 'methods') else 'N/A'
            print(f"  {path_str} - {methods}")
            notif_routes.append(path_str)
    
    if len(notif_routes) == 0:
        print("  (NINGUNA ENCONTRADA)")
    else:
        print(f"\\nTotal: {len(notif_routes)} rutas")
        if len(notif_routes) >= 4:
            print("✓ Todas las rutas esperadas están presentes")
        else:
            print(f"✗ Solo {len(notif_routes)}/4 rutas presentes")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
ENDPYTHON
'''
        
        stdin, stdout, stderr = client.exec_command(cmd)
        exit_code = stdout.channel.recv_exit_status()
        
        output = stdout.read().decode()
        error = stderr.read().decode()
        
        print("=" * 70)
        print(output)
        if error and "UserWarning" not in error:
            print(f"\nErrores:\n{error}")
        
    finally:
        client.close()

if __name__ == "__main__":
    check_routes_with_correct_venv()
