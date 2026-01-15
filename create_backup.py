#!/usr/bin/env python3
"""Script para crear backup completo del proyecto almacen-backend"""

import paramiko
import os
from datetime import datetime
import zipfile

SERVER = "192.168.180.164"
USER = "administrador"
PASSWORD = "DHumanos25"

# Configuración de backup
BACKUP_DATE = datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUP_DIR = f"c:\\Users\\Programador1\\backups\\almacen-backend_{BACKUP_DATE}"
DB_NAME = "almacen_db"
DB_USER = "postgres"

def create_local_backup():
    """Crea backup de archivos locales"""
    print("=" * 70)
    print("1. BACKUP DE CÓDIGO LOCAL")
    print("=" * 70)
    
    os.makedirs(BACKUP_DIR, exist_ok=True)
    print(f"✓ Directorio de backup creado: {BACKUP_DIR}")
    
    # Crear ZIP del código
    source_dir = r"c:\Users\Programador1\almacen-backend"
    zip_path = os.path.join(BACKUP_DIR, "codigo_fuente.zip")
    
    print(f"\nCreando ZIP del código fuente...")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_dir):
            # Excluir directorios innecesarios
            dirs[:] = [d for d in dirs if d not in ['.venv', 'venv', '__pycache__', '.git', 'node_modules']]
            
            for file in files:
                if not file.endswith('.pyc'):
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, source_dir)
                    zipf.write(file_path, arcname)
                    
    size_mb = os.path.getsize(zip_path) / (1024 * 1024)
    print(f"✓ Código fuente empaquetado: {size_mb:.2f} MB")
    
    return zip_path

def backup_database_remote():
    """Hace backup de la base de datos desde el servidor"""
    print("\n" + "=" * 70)
    print("2. BACKUP DE BASE DE DATOS (Servidor)")
    print("=" * 70)
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(SERVER, username=USER, password=PASSWORD, allow_agent=False, look_for_keys=False)
        print(f"✓ Conectado a {SERVER}")
        
        # Crear dump de la base de datos
        remote_backup = f"/tmp/almacen_db_backup_{BACKUP_DATE}.sql"
        print(f"\nCreando dump de base de datos...")
        
        # Dump completo con datos
        stdin, stdout, stderr = client.exec_command(
            f"pg_dump -U {DB_USER} -h localhost {DB_NAME} > {remote_backup} 2>&1"
        )
        exit_code = stdout.channel.recv_exit_status()
        output = stdout.read().decode()
        error = stderr.read().decode()
        
        if exit_code == 0:
            # Verificar tamaño
            stdin, stdout, stderr = client.exec_command(f"ls -lh {remote_backup}")
            size_info = stdout.read().decode().strip()
            print(f"✓ Dump creado: {size_info.split()[4]}")
            
            # Descargar el archivo
            local_db_backup = os.path.join(BACKUP_DIR, f"database_backup_{BACKUP_DATE}.sql")
            sftp = client.open_sftp()
            
            print(f"Descargando base de datos...")
            sftp.get(remote_backup, local_db_backup)
            sftp.close()
            
            size_mb = os.path.getsize(local_db_backup) / (1024 * 1024)
            print(f"✓ Base de datos descargada: {size_mb:.2f} MB")
            
            # Limpiar archivo temporal
            stdin, stdout, stderr = client.exec_command(f"rm {remote_backup}")
            stdout.channel.recv_exit_status()
            
            return local_db_backup
        else:
            print(f"✗ Error en pg_dump: {output} {error}")
            return None
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return None
    finally:
        client.close()

def create_postman_instructions():
    """Crea archivo con instrucciones para exportar Postman"""
    print("\n" + "=" * 70)
    print("3. INSTRUCCIONES PARA BACKUP DE POSTMAN")
    print("=" * 70)
    
    instructions = f"""INSTRUCCIONES PARA BACKUP DE POSTMAN
========================================
Fecha: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Para exportar tus colecciones de Postman:

1. Abre Postman
2. En el panel izquierdo, haz clic en "Collections"
3. Para cada colección:
   a. Haz clic en los 3 puntos (...) junto al nombre de la colección
   b. Selecciona "Export"
   c. Elige "Collection v2.1 (recomendado)"
   d. Haz clic en "Export"
   e. Guarda el archivo en: {BACKUP_DIR}\\postman\\

4. Para exportar el Environment:
   a. Haz clic en el icono de configuración (⚙️) en la esquina superior derecha
   b. Selecciona "Environments"
   c. Haz clic en el botón "..." junto al environment
   d. Selecciona "Export"
   e. Guarda el archivo en: {BACKUP_DIR}\\postman\\

5. ALTERNATIVA - Exportar TODO:
   a. Ve a Settings (⚙️)
   b. Selecciona la pestaña "Data"
   c. Haz clic en "Export Data"
   d. Esto exportará todas las colecciones, environments, etc.
   e. Guarda el archivo en: {BACKUP_DIR}\\postman\\

NOTA: Si estás usando Postman con cuenta en la nube, tus colecciones
ya están respaldadas automáticamente en tu cuenta.

Para VSCode con extensión Postman:
- Los archivos .http están en: app/frontend/ (si existen)
- Las configuraciones están en: .vscode/ (si existe)
"""
    
    postman_dir = os.path.join(BACKUP_DIR, "postman")
    os.makedirs(postman_dir, exist_ok=True)
    
    instructions_file = os.path.join(postman_dir, "INSTRUCCIONES_POSTMAN.txt")
    with open(instructions_file, 'w', encoding='utf-8') as f:
        f.write(instructions)
    
    print(f"✓ Instrucciones creadas en: {postman_dir}")
    print("\nNOTA: Debes exportar manualmente las colecciones de Postman")
    print("      siguiendo las instrucciones en INSTRUCCIONES_POSTMAN.txt")
    
    return instructions_file

def backup_server_configs():
    """Backup de configuraciones del servidor"""
    print("\n" + "=" * 70)
    print("4. BACKUP DE CONFIGURACIONES DEL SERVIDOR")
    print("=" * 70)
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(SERVER, username=USER, password=PASSWORD, allow_agent=False, look_for_keys=False)
        
        configs_dir = os.path.join(BACKUP_DIR, "server_configs")
        os.makedirs(configs_dir, exist_ok=True)
        
        # Archivos de configuración a respaldar
        config_files = [
            "/etc/systemd/system/almacen-backend.service",
            "/opt/almacen-backend/.env",
            "/opt/almacen-backend/requirements.txt",
        ]
        
        sftp = client.open_sftp()
        
        for remote_file in config_files:
            try:
                filename = os.path.basename(remote_file)
                local_file = os.path.join(configs_dir, filename)
                
                sftp.get(remote_file, local_file)
                print(f"✓ {filename}")
            except Exception as e:
                print(f"⚠ {filename}: {str(e)[:50]}")
        
        sftp.close()
        
        # Guardar info del sistema
        system_info_file = os.path.join(configs_dir, "system_info.txt")
        
        commands = [
            ("Python version", "python3 --version"),
            ("Pip packages", "/opt/almacen-backend/venv/bin/pip list"),
            ("PostgreSQL version", "psql --version"),
            ("Service status", "systemctl status almacen-backend --no-pager"),
            ("Disk usage", "df -h /opt/almacen-backend"),
        ]
        
        with open(system_info_file, 'w', encoding='utf-8') as f:
            f.write(f"INFORMACIÓN DEL SISTEMA - {datetime.now()}\n")
            f.write("=" * 70 + "\n\n")
            
            for desc, cmd in commands:
                f.write(f"\n{desc}:\n")
                f.write("-" * 40 + "\n")
                stdin, stdout, stderr = client.exec_command(cmd)
                output = stdout.read().decode()
                f.write(output)
                f.write("\n")
        
        print(f"✓ Información del sistema guardada")
        
    except Exception as e:
        print(f"✗ Error: {e}")
    finally:
        client.close()

def create_restore_instructions():
    """Crea instrucciones de restauración"""
    print("\n" + "=" * 70)
    print("5. CREANDO INSTRUCCIONES DE RESTAURACIÓN")
    print("=" * 70)
    
    instructions = f"""INSTRUCCIONES DE RESTAURACIÓN
================================
Fecha del backup: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

CONTENIDO DEL BACKUP:
- codigo_fuente.zip: Código completo del proyecto
- database_backup_{BACKUP_DATE}.sql: Dump de PostgreSQL
- server_configs/: Archivos de configuración del servidor
- postman/: Colecciones de Postman (a exportar manualmente)

RESTAURACIÓN PASO A PASO:
==========================

1. RESTAURAR CÓDIGO:
   - Descomprimir codigo_fuente.zip en la ubicación deseada
   - cd almacen-backend
   - python -m venv venv
   - venv\\Scripts\\activate  (Windows) o source venv/bin/activate (Linux)
   - pip install -r requirements.txt

2. RESTAURAR BASE DE DATOS:
   En el servidor PostgreSQL:
   
   # Crear base de datos
   createdb -U postgres almacen_db
   
   # Restaurar dump
   psql -U postgres -d almacen_db -f database_backup_{BACKUP_DATE}.sql
   
   # Verificar
   psql -U postgres -d almacen_db -c "\\dt"

3. CONFIGURAR SERVIDOR:
   - Copiar .env al directorio del proyecto
   - Copiar almacen-backend.service a /etc/systemd/system/
   - sudo systemctl daemon-reload
   - sudo systemctl enable almacen-backend
   - sudo systemctl start almacen-backend

4. VERIFICAR:
   - systemctl status almacen-backend
   - curl http://localhost:8081/api
   - Abrir navegador en http://servidor:8081/dashboard

5. IMPORTAR POSTMAN:
   - Abrir Postman
   - Settings > Data > Import Data
   - Seleccionar archivos .json de la carpeta postman/

NOTAS IMPORTANTES:
==================
- Verificar que las URLs en .env coincidan con tu entorno
- Ajustar permisos de archivos si es necesario
- Revisar que PostgreSQL esté corriendo antes de restaurar
- Cambiar contraseñas de producción después de restaurar

CONTACTO DE SOPORTE:
- Revisar logs: journalctl -u almacen-backend -f
- Logs de base de datos: /var/log/postgresql/
"""
    
    restore_file = os.path.join(BACKUP_DIR, "INSTRUCCIONES_RESTAURACION.txt")
    with open(restore_file, 'w', encoding='utf-8') as f:
        f.write(instructions)
    
    print(f"✓ Instrucciones creadas")
    
    return restore_file

def create_summary():
    """Crea resumen del backup"""
    print("\n" + "=" * 70)
    print("RESUMEN DEL BACKUP")
    print("=" * 70)
    
    summary = f"""BACKUP COMPLETADO
=================
Fecha: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Ubicación: {BACKUP_DIR}

ARCHIVOS INCLUIDOS:
"""
    
    total_size = 0
    for root, dirs, files in os.walk(BACKUP_DIR):
        for file in files:
            file_path = os.path.join(root, file)
            size = os.path.getsize(file_path)
            total_size += size
            rel_path = os.path.relpath(file_path, BACKUP_DIR)
            size_mb = size / (1024 * 1024)
            summary += f"\n  - {rel_path} ({size_mb:.2f} MB)"
    
    summary += f"\n\nTAMAÑO TOTAL: {total_size / (1024 * 1024):.2f} MB"
    summary += f"\n\nPara restaurar, consulta: INSTRUCCIONES_RESTAURACION.txt"
    
    summary_file = os.path.join(BACKUP_DIR, "RESUMEN_BACKUP.txt")
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(summary)
    
    print(summary)
    print(f"\n✓ Resumen guardado en: RESUMEN_BACKUP.txt")

def main():
    """Ejecuta el backup completo"""
    print("\n" + "=" * 70)
    print("BACKUP COMPLETO DEL PROYECTO ALMACEN-BACKEND")
    print("=" * 70)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Destino: {BACKUP_DIR}")
    print("=" * 70)
    
    try:
        # 1. Backup de código local
        create_local_backup()
        
        # 2. Backup de base de datos
        backup_database_remote()
        
        # 3. Instrucciones Postman
        create_postman_instructions()
        
        # 4. Configuraciones del servidor
        backup_server_configs()
        
        # 5. Instrucciones de restauración
        create_restore_instructions()
        
        # 6. Resumen
        create_summary()
        
        print("\n" + "=" * 70)
        print("✓✓✓ BACKUP COMPLETADO EXITOSAMENTE ✓✓✓")
        print("=" * 70)
        print(f"\nUbicación del backup: {BACKUP_DIR}")
        print("\nPróximos pasos:")
        print("1. Revisar el contenido del backup")
        print("2. Exportar colecciones de Postman (ver instrucciones)")
        print("3. Guardar el backup en un lugar seguro (USB, nube, etc.)")
        print("4. Opcionalmente, crear un ZIP del directorio completo")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error durante el backup: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
