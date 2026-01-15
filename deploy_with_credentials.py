#!/usr/bin/env python3
"""Script para desplegar notificaciones con autenticación SSH"""

import subprocess
import sys
import time
from pathlib import Path

# Credenciales del servidor
SERVER = "192.168.180.164"
USER = "administrador"
PASSWORD = "DHumanos25"

def run_ssh_command(cmd, description=""):
    """Ejecuta un comando via SSH en el servidor"""
    if description:
        print(f"\n{description}...")
    
    try:
        # Usar ssh con esperado para pasar la contraseña
        # Construir el comando SSH
        full_cmd = f'ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null {USER}@{SERVER} "{cmd}"'
        
        # Usar plink de PuTTY si está disponible
        plink_cmd = f'plink.exe -ssh -l {USER} -pw {PASSWORD} -batch {SERVER} "{cmd}"'
        
        # Intentar con plink primero (mejor para Windows)
        result = subprocess.run(plink_cmd, shell=True, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print(f"✓ Comando ejecutado exitosamente")
            if result.stdout:
                print(f"Salida: {result.stdout.strip()}")
            return True
        else:
            # Si falla plink, mostrar el error
            if "not recognized" in result.stderr:
                print(f"⚠ plink.exe no encontrado, usando sshpass...")
                # Intentar con sshpass (si existe en el PATH)
                sshpass_cmd = f'sshpass -p "{PASSWORD}" ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null {USER}@{SERVER} "{cmd}"'
                result = subprocess.run(sshpass_cmd, shell=True, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    print(f"✓ Comando ejecutado exitosamente")
                    if result.stdout:
                        print(f"Salida: {result.stdout.strip()}")
                    return True
            
            print(f"✗ Error ejecutando comando: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"✗ Timeout ejecutando comando")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def deploy():
    """Ejecuta el deployment"""
    print("\n" + "=" * 70)
    print("DEPLOYMENT: Actualización de Notificaciones")
    print(f"Servidor: {SERVER}")
    print(f"Usuario: {USER}")
    print("=" * 70)
    
    # 1. Git pull
    if not run_ssh_command(
        "cd /opt/almacen-backend && git pull origin main",
        "1. Obteniendo cambios de GitHub"
    ):
        print("✗ Fallo en git pull")
        return False
    
    # 2. Reiniciar servicio
    if not run_ssh_command(
        "systemctl restart almacen-backend",
        "2. Reiniciando servicio almacen-backend"
    ):
        print("✗ Fallo en reinicio de servicio")
        return False
    
    # 3. Esperar a que inicie
    time.sleep(3)
    
    # 4. Verificar estado
    if not run_ssh_command(
        "systemctl is-active almacen-backend",
        "3. Verificando estado del servicio"
    ):
        print("✗ Servicio no está corriendo")
        # Ver los logs de error
        run_ssh_command(
            "journalctl -u almacen-backend -n 20",
            "   Logs del servicio"
        )
        return False
    
    # 5. Probar endpoint
    if not run_ssh_command(
        'curl -s -X GET "http://127.0.0.1:8081/api/v1/requisiciones/notificaciones?solo_no_leidas=false" -H "Authorization: Bearer test" | head -c 200',
        "4. Probando endpoint de notificaciones"
    ):
        print("✗ Fallo al probar endpoint")
        return False
    
    print("\n" + "=" * 70)
    print("✓ DEPLOYMENT COMPLETADO EXITOSAMENTE")
    print("=" * 70)
    print("\nPróximos pasos:")
    print("1. Abre http://192.168.180.164:8081/dashboard en tu navegador")
    print("2. Verifica que las notificaciones cargan sin error 404")
    print("3. Intenta marcar notificaciones como leídas")
    
    return True

if __name__ == "__main__":
    try:
        success = deploy()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n✗ Deployment cancelado por el usuario")
        sys.exit(1)
