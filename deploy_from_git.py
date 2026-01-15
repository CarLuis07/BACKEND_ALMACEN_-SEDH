#!/usr/bin/env python3
"""Script para desplegar desde GitHub en el servidor"""
import subprocess
import sys

def run_command(cmd, description=""):
    """Ejecuta un comando y retorna el resultado"""
    if description:
        print(f"\n{description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            if description:
                print(f"✓ {description} - OK")
            return True
        else:
            print(f"✗ Error: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print(f"✗ Timeout en: {cmd}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def deploy_from_git():
    """Despliega los cambios desde GitHub"""
    print("=" * 60)
    print("DEPLOYMENT: Actualización de Notificaciones desde Git")
    print("=" * 60)
    
    # 1. Navegar al directorio del backend
    os.chdir("/opt/almacen-backend")
    
    # 2. Hacer pull del repositorio
    if not run_command("git pull origin main", "1. Obteniendo cambios de GitHub"):
        return False
    
    # 3. Reiniciar servicio
    if not run_command("systemctl restart almacen-backend", "2. Reiniciando servicio almacen-backend"):
        return False
    
    # 4. Esperar a que el servicio inicie
    import time
    time.sleep(3)
    
    # 5. Verificar estado del servicio
    result = subprocess.run("systemctl is-active almacen-backend", shell=True, capture_output=True, text=True)
    if result.stdout.strip() == "active":
        print("✓ Servicio activo")
    else:
        print(f"✗ Servicio no activo: {result.stdout.strip()}")
        return False
    
    # 6. Probar el endpoint
    result = subprocess.run(
        'curl -s -X GET "http://127.0.0.1:8081/api/v1/requisiciones/notificaciones?solo_no_leidas=false" '
        '-H "Authorization: Bearer test" 2>&1 | head -c 100',
        shell=True, capture_output=True, text=True, timeout=10
    )
    print(f"\n3. Probando endpoint:")
    print(f"   Respuesta: {result.stdout[:100]}...")
    
    print("\n" + "=" * 60)
    print("✓ DEPLOYMENT EXITOSO")
    print("=" * 60)
    return True

if __name__ == "__main__":
    import os
    success = deploy_from_git()
    sys.exit(0 if success else 1)
