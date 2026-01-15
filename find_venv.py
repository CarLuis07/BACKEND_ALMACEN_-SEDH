#!/usr/bin/env python3
"""Verificar rutas usando el venv del servicio"""

import paramiko

SERVER = "192.168.180.164"
USER = "administrador"  
PASSWORD = "DHumanos25"

def check_venv_location():
    """Busca dónde está el venv del servicio"""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(SERVER, username=USER, password=PASSWORD, allow_agent=False, look_for_keys=False)
        
        # Ver el archivo unit del servicio para encontrar el venv
        print("Contenido del servicio almacen-backend:")
        stdin, stdout, stderr = client.exec_command(
            "systemctl cat almacen-backend 2>&1 | grep -E 'ExecStart|Environment|WorkingDirectory' | head -10"
        )
        output = stdout.read().decode()
        print(output)
        
        # Buscar venvs en /opt/almacen-backend
        print("\nBuscando venvs:")
        stdin, stdout, stderr = client.exec_command(
            "find /opt/almacen-backend -name 'python*' -o -name 'activate' 2>/dev/null | head -10"
        )
        output = stdout.read().decode()
        print(output)
        
        # Ver qué python está corriendo el servicio
        print("\nProceso del servicio:")
        stdin, stdout, stderr = client.exec_command(
            "ps aux | grep almacen | grep -v grep"
        )
        output = stdout.read().decode()
        print(output[:500])
        
    finally:
        client.close()

if __name__ == "__main__":
    check_venv_location()
