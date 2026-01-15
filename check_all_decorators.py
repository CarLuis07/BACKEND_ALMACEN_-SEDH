#!/usr/bin/env python3
"""Verificar todos los decoradores en el servidor"""

import paramiko

SERVER = "192.168.180.164"
USER = "administrador"  
PASSWORD = "DHumanos25"

def check_all_decorators():
    """Verifica que todos los decoradores están en el servidor"""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(SERVER, username=USER, password=PASSWORD, allow_agent=False, look_for_keys=False)
        
        # Buscar todos los decoradores @router.put/@router.post
        stdin, stdout, stderr = client.exec_command(
            'grep -E "@router\\.(get|put|post).*notificaciones" /opt/almacen-backend/app/api/requisiciones/router.py'
        )
        decorators = stdout.read().decode()
        
        print("Decoradores encontrados en servidor:")
        print("=" * 70)
        if decorators:
            for i, line in enumerate(decorators.strip().split('\n'), 1):
                print(f"{i}. {line}")
        else:
            print("(ninguno encontrado)")
        
        # Mostrar líneas 2860-2875 para ver si el segundo decorador está
        print("\nLíneas 2860-2875:")
        print("=" * 70)
        stdin, stdout, stderr = client.exec_command(
            "sed -n '2860,2875p' /opt/almacen-backend/app/api/requisiciones/router.py"
        )
        output = stdout.read().decode()
        for i, line in enumerate(output.split('\n'), 2860):
            if line:
                print(f"{i:4d}: {line}")
        
        # Mostrar líneas 2900-2910
        print("\nLíneas 2900-2910:")
        print("=" * 70)
        stdin, stdout, stderr = client.exec_command(
            "sed -n '2900,2910p' /opt/almacen-backend/app/api/requisiciones/router.py"
        )
        output = stdout.read().decode()
        for i, line in enumerate(output.split('\n'), 2900):
            if line:
                print(f"{i:4d}: {line}")
        
    finally:
        client.close()

if __name__ == "__main__":
    check_all_decorators()
