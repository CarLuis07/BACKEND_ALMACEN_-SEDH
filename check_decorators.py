#!/usr/bin/env python3
"""Verificar decoradores en el router"""

import paramiko

SERVER = "192.168.180.164"
USER = "administrador"  
PASSWORD = "DHumanos25"

def check_decorators():
    """Verifica los decoradores antes de la función"""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(SERVER, username=USER, password=PASSWORD, allow_agent=False, look_for_keys=False)
        
        # Obtener líneas alrededor de la función
        stdin, stdout, stderr = client.exec_command(
            "sed -n '2805,2825p' /opt/almacen-backend/app/api/requisiciones/router.py"
        )
        
        output = stdout.read().decode('utf-8')
        
        print("Líneas 2805-2825 del router.py:")
        print("=" * 70)
        for i, line in enumerate(output.split('\n'), 2805):
            print(f"{i:4d}: {line}")
        print("=" * 70)
        
        # Verificar que hay @router decorador
        stdin, stdout, stderr = client.exec_command(
            "grep -B2 'def api_listar_notificaciones' /opt/almacen-backend/app/api/requisiciones/router.py | head -5"
        )
        
        output = stdout.read().decode('utf-8')
        print("\nLíneas antes de api_listar_notificaciones:")
        print(output)
        
    finally:
        client.close()

if __name__ == "__main__":
    check_decorators()
