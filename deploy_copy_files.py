#!/usr/bin/env python3
"""Script para desplegar copiar archivos y reiniciar servicio"""

import subprocess
import sys
import time

# Credenciales del servidor
SERVER = "192.168.180.164"
USER = "administrador"
PASSWORD = "DHumanos25"

# Archivos a desplegar
FILES = [
    {
        "local": r"c:\Users\Programador1\almacen-backend\app\api\requisiciones\router.py",
        "remote": "/opt/almacen-backend/app/api/requisiciones/router.py"
    },
    {
        "local": r"c:\Users\Programador1\almacen-backend\app\frontend\dashboard.html",
        "remote": "/opt/almacen-backend/app/frontend/dashboard.html"
    }
]

def run_command(description, cmd, show_output=True):
    """Ejecuta un comando local o remoto"""
    print(f"\n{description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            print(f"✓ Éxito")
            if show_output and result.stdout:
                output = result.stdout.strip()
                if len(output) > 200:
                    print(f"  {output[:200]}...")
                else:
                    print(f"  {output}")
            return True
        else:
            if result.stderr:
                print(f"✗ Error: {result.stderr}")
            else:
                print(f"✗ Error: {result.stdout}")
            return False
    except subprocess.TimeoutExpired:
        print(f"✗ Timeout")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def deploy():
    """Ejecuta el deployment"""
    print("\n" + "=" * 70)
    print("DEPLOYMENT: Actualización de Notificaciones (Copiar archivos)")
    print(f"Servidor: {SERVER}")
    print(f"Usuario: {USER}")
    print("=" * 70)
    
    # 1. Copiar archivos usando plink + SCP
    for file_info in FILES:
        local = file_info["local"]
        remote = file_info["remote"]
        
        # Usar pscp de PuTTY
        pscp_cmd = f'pscp.exe -l {USER} -pw {PASSWORD} "{local}" {USER}@{SERVER}:{remote}'
        
        if not run_command(f"Copiando {local.split(chr(92))[-1]}", pscp_cmd):
            print(f"⚠ Intentando con scp alternativo...")
            # Alternativa con scp
            scp_cmd = f'scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o "User {USER}" "{local}" {SERVER}:{remote}'
            if not run_command(f"Copiando {local.split(chr(92))[-1]} (intento 2)", scp_cmd, show_output=False):
                return False
    
    # 2. Cambiar permisos y reiniciar servicio
    print("\n2. Preparando servidor...")
    
    # Dar permisos correctos
    plink_cmd = f'plink.exe -ssh -l {USER} -pw {PASSWORD} -batch {SERVER} "sudo chown -R www-data:www-data /opt/almacen-backend/app 2>/dev/null || true && sudo systemctl restart almacen-backend"'
    
    if not run_command("Reiniciando servicio", plink_cmd):
        print("⚠ Intentando solo reinicio sin sudo...")
        plink_cmd = f'plink.exe -ssh -l {USER} -pw {PASSWORD} -batch {SERVER} "systemctl restart almacen-backend 2>&1 || echo Reinicio iniciado"'
        run_command("Reinicio del servicio", plink_cmd, show_output=False)
    
    # 3. Esperar
    time.sleep(4)
    
    # 4. Verificar
    plink_cmd = f'plink.exe -ssh -l {USER} -pw {PASSWORD} -batch {SERVER} "systemctl is-active almacen-backend"'
    
    if run_command("Verificando estado del servicio", plink_cmd):
        # 5. Probar endpoint
        plink_cmd = f'plink.exe -ssh -l {USER} -pw {PASSWORD} -batch {SERVER} "curl -s -X GET http://127.0.0.1:8081/api/v1/requisiciones/notificaciones -H Authorization:\\ Bearer\\ test 2>&1 | head -c 100"'
        run_command("Probando endpoint", plink_cmd)
        
        print("\n" + "=" * 70)
        print("✓ DEPLOYMENT COMPLETADO EXITOSAMENTE")
        print("=" * 70)
        print("\nPróximos pasos:")
        print("1. Abre http://192.168.180.164:8081/dashboard en tu navegador")
        print("2. Verifica que las notificaciones cargan sin error 404")
        print("3. Intenta marcar notificaciones como leídas")
        
        return True
    else:
        print("\n✗ El servicio no está corriendo")
        print("Intenta reiniciar manualmente:")
        print(f"  ssh {USER}@{SERVER}")
        print(f"  sudo systemctl restart almacen-backend")
        return False

if __name__ == "__main__":
    try:
        success = deploy()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n✗ Deployment cancelado por el usuario")
        sys.exit(1)
