#!/usr/bin/env python3
"""Script múltiple para desplegar a servidor - intenta varios métodos"""

import subprocess
import sys
import os
from pathlib import Path

def run_git_pull():
    """Intenta desplegar via git pull en el servidor"""
    print("\n" + "=" * 60)
    print("MÉTODO 1: Git Pull en servidor remoto")
    print("=" * 60)
    
    try:
        # Usar SSH nativo de windows/git
        cmd = [
            "ssh", 
            "-i", Path.home() / ".ssh" / "id_rsa",
            "root@192.168.180.164",
            "cd /opt/almacen-backend && git pull origin main && systemctl restart almacen-backend && sleep 2 && systemctl is-active almacen-backend"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            print("✓ Deployment exitoso")
            print(result.stdout)
            return True
        else:
            print(f"✗ Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ Error en método 1: {e}")
        return False

def manual_instructions():
    """Muestra instrucciones manuales"""
    print("\n" + "=" * 60)
    print("INSTRUCCIONES MANUALES DE DEPLOYMENT")
    print("=" * 60)
    
    instructions = """
1. Conectarse al servidor via SSH:
   ssh root@192.168.180.164

2. Desplegar cambios:
   cd /opt/almacen-backend
   git pull origin main
   systemctl restart almacen-backend
   sleep 3
   systemctl is-active almacen-backend

3. Verificar que funciona:
   curl -X GET "http://127.0.0.1:8081/api/v1/requisiciones/notificaciones" \
     -H "Authorization: Bearer test"

4. Si falla, ver logs:
   journalctl -u almacen-backend -n 50 -f

CAMBIOS DESPLEGADOS:
- app/api/requisiciones/router.py: 3 nuevos endpoints proxy para notificaciones
- app/frontend/dashboard.html: URLs actualizadas para usar nuevos endpoints

COMMIT EN GITHUB:
- fbc6788: feat: add notificaciones proxy endpoints to requisiciones router
"""
    
    print(instructions)

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("DEPLOYMENT: Actualización de Notificaciones")
    print("=" * 60)
    
    # Intentar método 1
    if run_git_pull():
        sys.exit(0)
    
    # Si falla, mostrar instrucciones manuales
    print("\nNo se pudo realizar deployment automático.")
    manual_instructions()
    
    print("\n⚠ Por favor, ejecute los comandos anteriores manualmente en el servidor.")
    sys.exit(1)
