#!/usr/bin/env python3
"""Script para hacer backup completo del proyecto"""

import paramiko
import os
import shutil
import datetime
from pathlib import Path

SERVER = "192.168.180.164"
USER = "administrador"  
PASSWORD = "DHumanos25"

# Crear directorio de backup local
backup_date = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
backup_dir = Path(f"backup_{backup_date}")
backup_dir.mkdir(exist_ok=True)

print("=" * 70)
print(f"CREANDO BACKUP COMPLETO - {backup_date}")
print("=" * 70)

# Conectar al servidor
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    client.connect(SERVER, username=USER, password=PASSWORD, allow_agent=False, look_for_keys=False)
    
    # 1. Backup del código backend
    print("\n1. Creando backup del código backend...")
    stdin, stdout, stderr = client.exec_command(
        "cd /opt && sudo tar -czf /tmp/almacen-backend.tar.gz almacen-backend/ 2>&1"
    )
    stdout.channel.recv_exit_status()
    output = stdout.read().decode()
    if "cannot open" not in output.lower():
        print("   ✓ Backup del backend creado")
    
    # 2. Backup de la base de datos PostgreSQL
    print("\n2. Creando backup de la base de datos...")
    stdin, stdout, stderr = client.exec_command(
        "sudo -u postgres pg_dump -Fc almacen_db > /tmp/almacen_db.backup 2>&1"
    )
    stdout.channel.recv_exit_status()
    output = stdout.read().decode()
    if output:
        print(f"   {output[:100]}")
    else:
        print("   ✓ Backup de base de datos creado")
    
    # 3. Verificar que los archivos se crearon
    print("\n3. Verificando archivos de backup...")
    stdin, stdout, stderr = client.exec_command(
        "ls -lh /tmp/almacen-backend.tar.gz /tmp/almacen_db.backup 2>&1"
    )
    output = stdout.read().decode()
    print(output)
    
    # 4. Descargar archivos
    sftp = client.open_sftp()
    
    print("\n4. Descargando archivos...")
    
    # Descargar backend
    try:
        print("   Descargando backend.tar.gz...")
        sftp.get("/tmp/almacen-backend.tar.gz", str(backup_dir / "almacen-backend.tar.gz"))
        print("   ✓ Backend descargado")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Descargar base de datos
    try:
        print("   Descargando almacen_db.backup...")
        sftp.get("/tmp/almacen_db.backup", str(backup_dir / "almacen_db.backup"))
        print("   ✓ Base de datos descargada")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    sftp.close()
    
    # 5. Copiar colecciones de Postman locales si existen
    print("\n5. Buscando colecciones de Postman locales...")
    postman_files = []
    for root, dirs, files in os.walk("."):
        for file in files:
            if "postman" in file.lower() and file.endswith(".json"):
                postman_files.append(os.path.join(root, file))
    
    if postman_files:
        postman_dir = backup_dir / "postman"
        postman_dir.mkdir(exist_ok=True)
        for file in postman_files:
            print(f"   ✓ Copiando {os.path.basename(file)}")
            shutil.copy(file, postman_dir / os.path.basename(file))
    else:
        print("   (no se encontraron colecciones locales)")
    
    # 6. Crear README con información del backup
    readme = f"""# BACKUP DEL PROYECTO ALMACÉN

Fecha: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Contenido del backup:

1. **almacen-backend.tar.gz** - Código fuente completo del backend
   - Directorio: /opt/almacen-backend
   - Incluye: app/, venv/, requirements.txt, etc.

2. **almacen_db.backup** - Base de datos PostgreSQL (formato custom)
   - Nombre de base de datos: almacen_db
   - Para restaurar: pg_restore -Fc -d almacen_db almacen_db.backup

3. **postman/** - Colecciones de Postman (si existen)

## Servidor de origen:
- IP: {SERVER}
- Usuario: {USER}

## Para restaurar en un servidor nuevo:

### Backend:
```bash
cd /opt
sudo tar -xzf almacen-backend.tar.gz
cd almacen-backend
```

### Base de datos:
```bash
sudo -u postgres pg_restore -Fc -d almacen_db almacen_db.backup
```

## Archivos importantes del backend:
- app/main.py - Punto de entrada de la aplicación
- app/api/ - Routers de la API
- app/core/config.py - Configuración
- requirements.txt - Dependencias de Python
"""
    
    with open(backup_dir / "README.md", "w") as f:
        f.write(readme)
    
    print("\n6. Información de backup creada en README.md")
    
    # 7. Crear archivo comprimido final
    print("\n7. Creando archivo comprimido final...")
    shutil.make_archive(
        f"backup_{backup_date}",
        "zip",
        ".",
        backup_dir.name
    )
    
    final_backup = f"backup_{backup_date}.zip"
    final_size = os.path.getsize(final_backup) / (1024*1024)
    
    print(f"\n" + "=" * 70)
    print("✓ BACKUP COMPLETADO EXITOSAMENTE")
    print("=" * 70)
    print(f"\nArchivo: {final_backup}")
    print(f"Tamaño: {final_size:.2f} MB")
    print(f"\nUbicación: {os.path.abspath(final_backup)}")
    print(f"\nArchivos en el backup:")
    print(f"  - almacen-backend.tar.gz (código fuente)")
    print(f"  - almacen_db.backup (base de datos)")
    print(f"  - postman/ (colecciones si existen)")
    print(f"  - README.md (instrucciones de restauración)")
    
finally:
    client.close()
