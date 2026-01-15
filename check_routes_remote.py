#!/usr/bin/env python3
"""Ejecutar verificación de rutas en el servidor remoto"""

import paramiko

SERVER = "192.168.180.164"
USER = "administrador"  
PASSWORD = "DHumanos25"

def check_routes_remote():
    """Verifica rutas ejecutando en el servidor"""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(SERVER, username=USER, password=PASSWORD, allow_agent=False, look_for_keys=False)
        
        # Buscar la instalación de Python en el servidor
        stdin, stdout, stderr = client.exec_command("which python3")
        python_path = stdout.read().decode().strip()
        
        print(f"Python encontrado: {python_path}")
        
        # Ejecutar el script de verificación
        cmd = f'''{python_path} -c "
import sys
sys.path.insert(0, '/opt/almacen-backend')
try:
    from app.main import app
    print('Rutas de notificaciones en FastAPI:')
    notif_count = 0
    for route in app.routes:
        if 'notificaciones' in str(route.path):
            methods = route.methods if hasattr(route, 'methods') else 'N/A'
            print(f'  {{route.path}} - {{methods}}')
            notif_count += 1
    if notif_count == 0:
        print('  (ninguna encontrada)')
    print(f'Total: {{notif_count}} rutas de notificaciones')
except Exception as e:
    print(f'Error: {{e}}')
    import traceback
    traceback.print_exc()
"'''
        
        stdin, stdout, stderr = client.exec_command(cmd)
        exit_code = stdout.channel.recv_exit_status()
        
        output = stdout.read().decode()
        error = stderr.read().decode()
        
        print(output)
        if error:
            print(f"Errores:\n{error}")
        
    finally:
        client.close()

if __name__ == "__main__":
    check_routes_remote()
