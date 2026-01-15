#!/usr/bin/env python3
"""Script para desplegar cambios al servidor"""
import paramiko
import os
import sys

# Configuración
SERVER_IP = "192.168.180.164"
SERVER_USER = "root"
SERVER_PATH = "/opt/almacen-backend"
LOCAL_REPO = r"c:\Users\Programador1\almacen-backend"

FILES_TO_DEPLOY = [
    {
        "local": os.path.join(LOCAL_REPO, "app", "api", "requisiciones", "router.py"),
        "remote": f"{SERVER_PATH}/app/api/requisiciones/router.py"
    },
    {
        "local": os.path.join(LOCAL_REPO, "app", "frontend", "dashboard.html"),
        "remote": f"{SERVER_PATH}/app/frontend/dashboard.html"
    }
]

def deploy():
    """Despliega los archivos al servidor"""
    print("=" * 60)
    print("DEPLOYMENT: Actualización de Notificaciones")
    print("=" * 60)
    
    # Crear cliente SSH
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"\n1. Conectando a {SERVER_IP}...")
        # Intentar con autenticación por clave primero, luego por contraseña
        try:
            ssh.connect(SERVER_IP, username=SERVER_USER, allow_agent=True, look_for_keys=True, timeout=5)
        except paramiko.ssh_exception.SSHException:
            # Si falla, pedir contraseña
            import getpass
            password = getpass.getpass(f"Contraseña para {SERVER_USER}@{SERVER_IP}: ")
            ssh.connect(SERVER_IP, username=SERVER_USER, password=password, timeout=5)
        
        print("   ✓ Conectado")
        
        # SCP los archivos
        sftp = ssh.open_sftp()
        
        for file_info in FILES_TO_DEPLOY:
            local = file_info["local"]
            remote = file_info["remote"]
            
            if not os.path.exists(local):
                print(f"   ✗ Archivo local no encontrado: {local}")
                return False
            
            print(f"\n2. Desplegando {os.path.basename(local)}...")
            size = os.path.getsize(local)
            print(f"   Tamaño: {size:,} bytes")
            sftp.put(local, remote)
            print(f"   ✓ Desplegado a {remote}")
        
        sftp.close()
        
        # Reiniciar servicio
        print(f"\n3. Reiniciando servicio almacen-backend...")
        stdin, stdout, stderr = ssh.exec_command("systemctl restart almacen-backend")
        exit_code = stdout.channel.recv_exit_status()
        
        if exit_code == 0:
            print("   ✓ Servicio reiniciado")
        else:
            print(f"   ✗ Error al reiniciar: {stderr.read().decode()}")
            return False
        
        # Esperar y verificar
        import time
        time.sleep(3)
        
        stdin, stdout, stderr = ssh.exec_command("systemctl is-active almacen-backend")
        status = stdout.read().decode().strip()
        
        if status == "active":
            print(f"   ✓ Servicio activo")
        else:
            print(f"   ✗ Servicio no activo: {status}")
            return False
        
        # Probar endpoint
        print(f"\n4. Probando endpoint...")
        stdin, stdout, stderr = ssh.exec_command(
            'curl -s -X GET "http://127.0.0.1:8081/api/v1/requisiciones/notificaciones?solo_no_leidas=false" '
            '-H "Authorization: Bearer test" | head -c 200'
        )
        response = stdout.read().decode()
        print(f"   Respuesta: {response[:100]}...")
        
        print("\n" + "=" * 60)
        print("✓ DEPLOYMENT EXITOSO")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        ssh.close()

if __name__ == "__main__":
    success = deploy()
    sys.exit(0 if success else 1)
