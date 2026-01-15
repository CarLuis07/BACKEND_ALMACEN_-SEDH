#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import os
import sys
import time

# Configuracion del servidor
SERVER_HOST = "192.168.180.164"
SERVER_USER = "administrador"
SERVER_PASSWORD = "DHumanos25"

# Archivos a copiar (local -> remote)
FILES_TO_COPY = {
    "app/api/requisiciones/router.py": "/tmp/app-api-requisiciones-router-dot-py",
    "app/utils/pdf.py": "/tmp/app-utils-pdf-dot-py",
    "app/frontend/requisiciones.html": "/tmp/app-frontend-requisiciones-dot-html",
    "requirements.txt": "/tmp/requirements-dot-txt",
}

# Mapeo de ubicaciones finales
FINAL_DESTINATIONS = {
    "/tmp/app-api-requisiciones-router-dot-py": "/opt/almacen-backend/app/api/requisiciones/router.py",
    "/tmp/app-utils-pdf-dot-py": "/opt/almacen-backend/app/utils/pdf.py",
    "/tmp/app-frontend-requisiciones-dot-html": "/opt/almacen-backend/app/frontend/requisiciones.html",
    "/tmp/requirements-dot-txt": "/opt/almacen-backend/requirements.txt",
}


def copy_files_to_server():
    """Copia archivos al servidor usando PSCP"""
    print("=" * 70)
    print("COPIANDO ARCHIVOS AL SERVIDOR")
    print("=" * 70)
    
    files_to_move = []
    
    for local_file, remote_temp_path in FILES_TO_COPY.items():
        if not os.path.exists(local_file):
            print(f"[ERROR] Archivo no encontrado: {local_file}")
            return False, []
        
        print(f"\n[ENVIANDO] {local_file}")
        
        cmd = [
            "pscp",
            "-pw", SERVER_PASSWORD,
            local_file,
            f"{SERVER_USER}@{SERVER_HOST}:{remote_temp_path}"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            print(f"[ERROR] No se pudo copiar {local_file}")
            print(f"Detalle: {result.stderr}")
            return False, []
        
        print(f"[OK] Copiado a {remote_temp_path}")
        files_to_move.append((remote_temp_path, FINAL_DESTINATIONS[remote_temp_path]))
    
    print("\n" + "=" * 70)
    print("[OK] TODOS LOS ARCHIVOS COPIADOS A /tmp")
    print("=" * 70)
    
    return True, files_to_move


def move_files_with_sudo(files_to_move):
    """Mueve archivos usando sudo en el servidor"""
    print("\n" + "=" * 70)
    print("MOVIENDO ARCHIVOS A UBICACION FINAL")
    print("=" * 70)
    
    # Crear script de movimiento con caracteres ASCII solo
    import tempfile
    move_script = "#!/bin/bash\n"
    move_script += "set -e\n"
    move_script += "echo '------- INICIANDO MOVIMIENTOS -------'\n\n"
    
    for temp_path, remote_path in files_to_move:
        dir_path = remote_path.rsplit('/', 1)[0]
        move_script += f"echo 'Creando directorio {dir_path}...'\n"
        move_script += f"sudo mkdir -p {dir_path}\n"
        move_script += f"echo 'Moviendo {temp_path} a {remote_path}...'\n"
        move_script += f"sudo mv {temp_path} {remote_path}\n"
        move_script += f"sudo chown almacen:almacen {remote_path}\n"
        move_script += f"echo '[OK] {remote_path}'\n"
        move_script += f"echo ''\n"
    
    move_script += "echo '------- MOVIMIENTOS COMPLETADOS -------'\n"
    
    # Crear archivo temporal en Windows usando encoding UTF-8
    try:
        import tempfile
        temp_dir = os.environ.get('TEMP', '.')
        with tempfile.NamedTemporaryFile(
            mode='w', 
            suffix='.sh', 
            delete=False, 
            dir=temp_dir,
            encoding='utf-8'
        ) as f:
            f.write(move_script)
            local_script_path = f.name
        print(f"\n[INFO] Script temporal creado: {local_script_path}")
    except Exception as e:
        print(f"[ERROR] No se pudo crear script temporal: {e}")
        return False
    
    # Copiar script a servidor
    script_path = "/tmp/move-files.sh"
    cmd = [
        "pscp",
        "-pw", SERVER_PASSWORD,
        local_script_path,
        f"{SERVER_USER}@{SERVER_HOST}:{script_path}"
    ]
    
    print("[INFO] Copiando script de movimiento al servidor...")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    
    if result.returncode != 0:
        print(f"[ERROR] No se pudo copiar script: {result.stderr}")
        try:
            os.unlink(local_script_path)
        except:
            pass
        return False
    
    print("[OK] Script copiado\n")
    
    # Ejecutar script con plink
    print("[INFO] Ejecutando movimientos con sudo...")
    plink_cmd = [
        "plink",
        "-pw", SERVER_PASSWORD,
        f"{SERVER_USER}@{SERVER_HOST}",
        f"bash {script_path}"
    ]
    
    result = subprocess.run(plink_cmd, capture_output=True, text=True, timeout=30)
    print(result.stdout)
    
    if result.returncode != 0:
        if result.stderr and "Access granted" not in result.stderr:
            print(f"[STDERR] {result.stderr}")
        print("[ERROR] Error en ejecucion de movimientos")
        try:
            os.unlink(local_script_path)
        except:
            pass
        return False
    
    # Limpiar archivo temporal
    try:
        os.unlink(local_script_path)
    except:
        pass
    
    print("\n" + "=" * 70)
    print("[OK] ARCHIVOS MOVIDOS CORRECTAMENTE")
    print("=" * 70)
    
    return True


def restart_service():
    """Reinicia el servicio almacen-backend"""
    print("\n" + "=" * 70)
    print("REINICIANDO SERVICIO")
    print("=" * 70)
    
    print("[INFO] Enviando comando de reinicio (esto puede tomar tiempo)...")
    
    plink_cmd = [
        "plink",
        "-pw", SERVER_PASSWORD,
        f"{SERVER_USER}@{SERVER_HOST}",
        "nohup bash -c 'echo DHumanos25 | sudo -S systemctl restart almacen-backend' > /tmp/restart.log 2>&1 &"
    ]
    
    try:
        result = subprocess.run(plink_cmd, capture_output=True, text=True, timeout=30)
        print("[OK] Comando de reinicio enviado")
    except subprocess.TimeoutExpired:
        print("[ADVERTENCIA] Timeout en comando de reinicio (es normal)")
    
    # Esperar a que el servicio inicie
    print("[INFO] Esperando inicio del servicio (5 segundos)...")
    time.sleep(5)
    
    # Verificar estado del servicio
    print("[INFO] Verificando estado del servicio...")
    check_cmd = [
        "plink",
        "-pw", SERVER_PASSWORD,
        f"{SERVER_USER}@{SERVER_HOST}",
        "systemctl status almacen-backend"
    ]
    
    try:
        result = subprocess.run(check_cmd, capture_output=True, text=True, timeout=10)
        print(result.stdout)
        if "active (running)" in result.stdout:
            print("\n" + "=" * 70)
            print("[OK] SERVICIO ESTA ACTIVO Y FUNCIONANDO")
            print("=" * 70)
            return True
        else:
            print("[ADVERTENCIA] Estado del servicio desconocido")
            return False
    except Exception as e:
        print(f"[ADVERTENCIA] No se pudo verificar estado: {e}")
        return False


def verify_endpoint():
    """Verifica que el endpoint este accesible"""
    print("\n" + "=" * 70)
    print("VERIFICANDO ENDPOINT")
    print("=" * 70)
    
    url = "http://192.168.180.164:8081/api/v1/test-todas"
    print(f"[INFO] Probando endpoint: {url}")
    
    try:
        import requests
        response = requests.get(url, timeout=5)
        
        # Esperamos 401 (autenticacion requerida) como indicador de que el endpoint existe
        if response.status_code == 401:
            print(f"[OK] Endpoint activo (codigo: {response.status_code})")
            return True
        elif response.status_code == 200:
            print(f"[OK] Endpoint activo (codigo: {response.status_code})")
            return True
        else:
            print(f"[ADVERTENCIA] Codigo inesperado: {response.status_code}")
            return False
    except Exception as e:
        print(f"[ERROR] No se pudo acceder al endpoint: {e}")
        return False


def main():
    """Ejecuta el deployment completo"""
    print("\n")
    print("*" * 70)
    print("* INICIANDO DEPLOYMENT DE FINALIZACION")
    print("*" * 70)
    
    # Paso 1: Copiar archivos
    success, files_to_move = copy_files_to_server()
    if not success:
        print("\n[FATAL] Fallo en copia de archivos. Abortando.")
        sys.exit(1)
    
    # Paso 2: Mover archivos con sudo
    if not move_files_with_sudo(files_to_move):
        print("\n[FATAL] Fallo en movimiento de archivos. Abortando.")
        sys.exit(1)
    
    # Paso 3: Reiniciar servicio
    if not restart_service():
        print("\n[ADVERTENCIA] Error al reiniciar servicio.")
        # No abortamos aqui porque el servicio puede estar en proceso de restart
    
    # Paso 4: Verificar endpoint
    time.sleep(2)
    if not verify_endpoint():
        print("\n[ADVERTENCIA] No se pudo verificar endpoint.")
    
    print("\n")
    print("*" * 70)
    print("* DEPLOYMENT COMPLETADO")
    print("*" * 70)
    print("\nSiguientes pasos:")
    print("1. Verificar que el servicio este corriendo: systemctl status almacen-backend")
    print("2. Probar el endpoint en el navegador")
    print("3. Hacer login en el dashboard")
    print("4. Probar funcionalidad de Finalizar Requisicion")
    print("\n")


if __name__ == "__main__":
    main()
