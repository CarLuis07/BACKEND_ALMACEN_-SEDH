#!/usr/bin/env python3
"""Verificar integridad del archivo router.py"""

import paramiko

SERVER = "192.168.180.164"
USER = "administrador"  
PASSWORD = "DHumanos25"

def check_file():
    """Verifica el archivo en el servidor"""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(SERVER, username=USER, password=PASSWORD, allow_agent=False, look_for_keys=False)
        
        # 1. Contar líneas
        stdin, stdout, stderr = client.exec_command(
            "wc -l /opt/almacen-backend/app/api/requisiciones/router.py"
        )
        lines_count = stdout.read().decode().strip()
        print(f"Líneas en archivo remoto: {lines_count}")
        
        # 2. Ver últimas líneas
        print("\nÚltimas 10 líneas:")
        stdin, stdout, stderr = client.exec_command(
            "tail -10 /opt/almacen-backend/app/api/requisiciones/router.py"
        )
        tail_output = stdout.read().decode()
        for line in tail_output.split('\n'):
            print(f"  {line}")
        
        # 3. Verificar que todos los endpoints proxy están presentes
        print("\nBuscando endpoints proxy...")
        endpoints = [
            "def api_listar_notificaciones",
            "def api_marcar_notif_leida",
            "def api_marcar_todas_leidas",
            "def api_enviar_notificaciones_pendientes"
        ]
        
        for endpoint in endpoints:
            stdin, stdout, stderr = client.exec_command(
                f"grep -c '{endpoint}' /opt/almacen-backend/app/api/requisiciones/router.py"
            )
            count = stdout.read().decode().strip()
            status = "✓" if count == "1" else "✗"
            print(f"  {status} {endpoint}: {count}")
        
        # 4. Buscar los decoradores @router.get
        print("\nBuscando decoradores @router.get...")
        stdin, stdout, stderr = client.exec_command(
            'grep -n "@router.get.*notificaciones" /opt/almacen-backend/app/api/requisiciones/router.py'
        )
        decorators = stdout.read().decode()
        for line in decorators.strip().split('\n'):
            if line:
                print(f"  {line}")
        
        # 5. Comparar con archivo local
        print("\nComparando hashsum...")
        stdin, stdout, stderr = client.exec_command(
            "md5sum /opt/almacen-backend/app/api/requisiciones/router.py"
        )
        remote_hash = stdout.read().decode().strip()
        
        import hashlib
        with open(r"c:\Users\Programador1\almacen-backend\app\api\requisiciones\router.py", "rb") as f:
            local_hash = hashlib.md5(f.read()).hexdigest()
        
        print(f"  Local:  {local_hash}")
        print(f"  Remote: {remote_hash}")
        
        if remote_hash.split()[0] == local_hash:
            print("  ✓ Los archivos son idénticos")
        else:
            print("  ✗ Los archivos NO son idénticos")
            
    finally:
        client.close()

if __name__ == "__main__":
    check_file()
