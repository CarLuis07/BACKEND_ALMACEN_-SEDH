#!/usr/bin/env python3
"""Reiniciar servicio y limpiar caché de Python"""

import paramiko
import time

SERVER = "192.168.180.164"
USER = "administrador"  
PASSWORD = "DHumanos25"

def force_restart():
    """Fuerza el reinicio del servicio eliminando caché"""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(SERVER, username=USER, password=PASSWORD, allow_agent=False, look_for_keys=False)
        
        print("1. Deteniendo servicio...")
        stdin, stdout, stderr = client.exec_command("systemctl stop almacen-backend")
        stdout.channel.recv_exit_status()
        time.sleep(2)
        
        print("2. Limpiando caché de Python...")
        stdin, stdout, stderr = client.exec_command(
            "find /opt/almacen-backend -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true"
        )
        stdout.channel.recv_exit_status()
        
        print("3. Eliminando archivos .pyc...")
        stdin, stdout, stderr = client.exec_command(
            "find /opt/almacen-backend -type f -name '*.pyc' -delete 2>/dev/null || true"
        )
        stdout.channel.recv_exit_status()
        
        print("4. Iniciando servicio...")
        stdin, stdout, stderr = client.exec_command("systemctl start almacen-backend")
        stdout.channel.recv_exit_status()
        
        time.sleep(4)
        
        print("5. Verificando estado...")
        stdin, stdout, stderr = client.exec_command("systemctl is-active almacen-backend")
        status = stdout.read().decode().strip()
        
        if status == "active":
            print("✓ Servicio activo")
        else:
            print(f"✗ Servicio no activo: {status}")
            
            # Mostrar logs
            print("\nÚltimos logs:")
            stdin, stdout, stderr = client.exec_command("journalctl -u almacen-backend -n 30 --no-pager")
            logs = stdout.read().decode()
            print(logs[-1000:])
            return False
        
        time.sleep(2)
        
        print("\n6. Probando endpoint...")
        stdin, stdout, stderr = client.exec_command(
            'curl -s -w "\\n%{http_code}" http://127.0.0.1:8081/api/v1/requisiciones/notificaciones -H "Authorization: Bearer test"'
        )
        response = stdout.read().decode().strip()
        lines = response.split('\n')
        
        if lines:
            http_code = lines[-1]
            body = '\n'.join(lines[:-1])
            
            print(f"HTTP Code: {http_code}")
            print(f"Body: {body[:150]}")
            
            if http_code in ["200", "401"]:
                print("\n✓ ¡ENDPOINT FUNCIONANDO!")
                return True
            else:
                print(f"\n✗ Error HTTP {http_code}")
                return False
        
    finally:
        client.close()

if __name__ == "__main__":
    force_restart()
