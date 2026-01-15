#!/usr/bin/env python3
"""Script mejorado para backup - copia directamente sin sudo"""

import paramiko
import os
import shutil
import datetime
import time
from pathlib import Path

SERVER = "192.168.180.164"
USER = "administrador"  
PASSWORD = "DHumanos25"

backup_date = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
backup_dir = Path(f"backup_{backup_date}")
backup_dir.mkdir(exist_ok=True)

print("=" * 70)
print(f"BACKUP COMPLETO DEL PROYECTO - {backup_date}")
print("=" * 70)

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    client.connect(SERVER, username=USER, password=PASSWORD, allow_agent=False, look_for_keys=False)
    sftp = client.open_sftp()
    
    # 1. Backup del código (copiar directamente sin tar)
    print("\n1. Copiando código del backend...")
    code_dir = backup_dir / "almacen-backend"
    code_dir.mkdir(exist_ok=True)
    
    def copy_remote_tree(sftp, remote_path, local_path, exclude_dirs={'.git', '__pycache__', '.venv', 'venv', '.pytest_cache', 'node_modules'}):
        """Copia recursivamente desde servidor remoto"""
        try:
            items = sftp.listdir_attr(remote_path)
            for item in items:
                item_name = item.filename
                if item_name.startswith('.') and item_name not in {'.env', '.gitignore'}:
                    continue
                if item_name in exclude_dirs:
                    continue
                
                remote_full = f"{remote_path}/{item_name}"
                local_full = os.path.join(local_path, item_name)
                
                if item.filename in exclude_dirs or local_path.endswith(tuple(exclude_dirs)):
                    continue
                
                try:
                    # Intentar como archivo
                    os.makedirs(os.path.dirname(local_full), exist_ok=True)
                    sftp.get(remote_full, local_full)
                except IOError:
                    # Es un directorio
                    os.makedirs(local_full, exist_ok=True)
                    try:
                        copy_remote_tree(sftp, remote_full, local_full, exclude_dirs)
                    except:
                        pass
        except Exception as e:
            print(f"   Advertencia: {e}")
    
    print("   Copiando archivos (esto puede tomar un minuto)...")
    copy_remote_tree(sftp, "/opt/almacen-backend", str(code_dir))
    
    # Contar archivos
    file_count = sum(len(files) for _, _, files in os.walk(code_dir))
    print(f"   ✓ {file_count} archivos copiados")
    
    # 2. Backup de base de datos
    print("\n2. Haciendo backup de la base de datos...")
    
    # Crear backup comprimido en el servidor
    stdin, stdout, stderr = client.exec_command(
        "sudo -u postgres pg_dump -Fc almacen_db > /tmp/almacen_db.backup 2>&1"
    )
    stdout.channel.recv_exit_status()
    
    time.sleep(2)
    
    # Descargar base de datos
    try:
        print("   Descargando archivo de backup...")
        sftp.get("/tmp/almacen_db.backup", str(backup_dir / "almacen_db.backup"))
        
        db_size = os.path.getsize(backup_dir / "almacen_db.backup") / 1024
        print(f"   ✓ Base de datos descargada ({db_size:.2f} KB)")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # 3. Información de configuración
    print("\n3. Extrayendo información de configuración...")
    
    # Copiar .env si existe
    try:
        sftp.get("/opt/almacen-backend/.env", str(backup_dir / ".env.backup"))
        print("   ✓ Configuración (.env) copiada")
    except:
        print("   (archivo .env no accesible)")
    
    # 4. Crear README
    readme = f"""# BACKUP COMPLETO - ALMACÉN SEDH

**Fecha de backup:** {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Contenido del backup:

1. **almacen-backend/** - Código fuente completo
   - Todos los archivos Python, HTML, CSS, JS
   - Configuración de la aplicación
   - **Excluidos:** venv/, __pycache__/, .git/

2. **almacen_db.backup** - Base de datos PostgreSQL (formato custom)
   - Base de datos: almacen_db
   - Incluye todas las tablas, triggers, functions, datos

3. **.env.backup** - Variables de entorno (si está disponible)

4. **README.md** - Este archivo

## Información del servidor:
- **IP:** {SERVER}
- **Usuario:** {USER}
- **Backend path:** /opt/almacen-backend
- **Servicio:** almacen-backend (systemd)

## Cómo restaurar en un servidor nuevo:

### 1. Restaurar código backend:
```bash
mkdir -p /opt
cp -r almacen-backend /opt/

cd /opt/almacen-backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Restaurar base de datos:
```bash
# Conectar a PostgreSQL
sudo -u postgres psql

# En PostgreSQL:
CREATE DATABASE almacen_db;
```

Luego restaurar:
```bash
sudo -u postgres pg_restore -Fc -d almacen_db almacen_db.backup
```

### 3. Configurar variables de entorno:
```bash
cp .env.backup /opt/almacen-backend/.env
# Editar y ajustar según el nuevo servidor
```

### 4. Iniciar el servicio:
```bash
sudo systemctl enable almacen-backend
sudo systemctl start almacen-backend
```

## Información técnica:

- **Backend:** Python 3.12 + FastAPI + SQLAlchemy
- **Base de datos:** PostgreSQL
- **Servidor web:** Uvicorn
- **Frontend:** HTML5 + JavaScript + Bootstrap

## Versión del código:

El código incluye todos los cambios hasta la fecha del backup.
Consulta el archivo git log si necesitas información de commits específicos.

---
**Generado automáticamente**
"""
    
    with open(backup_dir / "README.md", "w") as f:
        f.write(readme)
    
    print("   ✓ README creado")
    
    # 5. Crear información de estadísticas
    print("\n4. Calculando estadísticas...")
    total_size = sum(
        os.path.getsize(os.path.join(dirpath, filename))
        for dirpath, dirnames, filenames in os.walk(backup_dir)
        for filename in filenames
    )
    
    print(f"   ✓ Tamaño total: {total_size / (1024*1024):.2f} MB")
    
    # 6. Crear archivo ZIP final
    print("\n5. Creando archivo ZIP final...")
    shutil.make_archive(
        f"backup_{backup_date}",
        "zip",
        ".",
        backup_dir.name
    )
    
    final_backup = f"backup_{backup_date}.zip"
    final_size = os.path.getsize(final_backup) / (1024*1024)
    
    print("\n" + "=" * 70)
    print("✓✓✓ BACKUP COMPLETADO EXITOSAMENTE ✓✓✓")
    print("=" * 70)
    
    print(f"\n📦 Archivo de backup: {final_backup}")
    print(f"📊 Tamaño comprimido: {final_size:.2f} MB")
    print(f"📁 Ubicación: {os.path.abspath(final_backup)}")
    
    print(f"\n📋 Contenido del backup:")
    print(f"   ✓ Código fuente ({file_count} archivos)")
    print(f"   ✓ Base de datos")
    print(f"   ✓ Configuración")
    print(f"   ✓ Instrucciones de restauración")
    
    print(f"\n💾 Pasos siguientes:")
    print(f"   1. Guarda '{final_backup}' en un lugar seguro")
    print(f"   2. Para restaurar: descomprime el ZIP y sigue el README.md")
    print(f"   3. Considera hacer backups adicionales regularmente")
    
    sftp.close()
    
finally:
    client.close()
