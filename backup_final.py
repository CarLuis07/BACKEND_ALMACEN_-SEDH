#!/usr/bin/env python3
"""Backup usando tar en el servidor"""

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
print(f"BACKUP COMPLETO - {backup_date}")
print("=" * 70)

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    client.connect(SERVER, username=USER, password=PASSWORD, allow_agent=False, look_for_keys=False)
    sftp = client.open_sftp()
    
    # 1. Crear tar del código en el servidor
    print("\n1. Comprimiendo código del backend en el servidor...")
    stdin, stdout, stderr = client.exec_command(
        "cd /opt && tar --exclude='__pycache__' --exclude='*.pyc' --exclude='.venv' --exclude='venv' --exclude='.git' -czf /tmp/almacen-backend-code.tar.gz almacen-backend/"
    )
    stdout.channel.recv_exit_status()
    time.sleep(2)
    print("   ✓ Compresión completada")
    
    # 2. Backup de base de datos
    print("\n2. Haciendo dump de la base de datos...")
    stdin, stdout, stderr = client.exec_command(
        "sudo -u postgres pg_dump -Fc almacen_db > /tmp/almacen_db.backup"
    )
    stdout.channel.recv_exit_status()
    time.sleep(2)
    print("   ✓ Dump completado")
    
    # 3. Descargar archivos
    print("\n3. Descargando archivos de backup...")
    
    files_to_download = [
        ("/tmp/almacen-backend-code.tar.gz", "almacen-backend-code.tar.gz"),
        ("/tmp/almacen_db.backup", "almacen_db.backup"),
        ("/opt/almacen-backend/.env", ".env"),
    ]
    
    for remote_file, local_name in files_to_download:
        try:
            local_path = backup_dir / local_name
            print(f"   Descargando {local_name}...", end=" ")
            sftp.get(remote_file, str(local_path))
            size = os.path.getsize(local_path) / 1024
            print(f"✓ ({size:.1f} KB)")
        except FileNotFoundError:
            print(f"✗ (archivo no encontrado)")
        except Exception as e:
            print(f"✗ ({e})")
    
    # 4. Copiar colecciones de Postman locales
    print("\n4. Buscando colecciones de Postman...")
    postman_dir = backup_dir / "postman"
    postman_dir.mkdir(exist_ok=True)
    
    postman_copied = 0
    for root, dirs, files in os.walk("."):
        for file in files:
            if "postman" in file.lower() and file.endswith(".json"):
                src = os.path.join(root, file)
                dst = postman_dir / file
                shutil.copy(src, dst)
                postman_copied += 1
                print(f"   ✓ {file}")
    
    if postman_copied == 0:
        print("   (no se encontraron colecciones locales)")
    
    # 5. Crear README
    readme_content = f"""# BACKUP COMPLETO - ALMACÉN SEDH

**Fecha:** {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Servidor:** {SERVER}

## Contenido del Backup

### 1. almacen-backend-code.tar.gz
- Código fuente completo del backend
- Python 3.12 + FastAPI + SQLAlchemy
- Todos los routers, modelos, repositorios
- **Excluido:** venv/, __pycache__/, .git/

### 2. almacen_db.backup
- Base de datos PostgreSQL (formato custom de pg_dump)
- Contiene todas las tablas, datos, triggers, functions
- Base de datos: almacen_db

### 3. .env
- Variables de entorno de configuración
- **IMPORTANTE:** Contiene secretos - Mantener confidencial

### 4. postman/
- Colecciones de Postman (si existen)
- Endpoints y ejemplos de prueba

## Cómo Restaurar

### En un servidor Linux/Ubuntu nuevo:

**Paso 1: Restaurar código**
```bash
cd /opt
sudo tar -xzf almacen-backend-code.tar.gz

cd almacen-backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Paso 2: Crear base de datos PostgreSQL**
```bash
sudo -u postgres createdb almacen_db
```

**Paso 3: Restaurar datos de la base de datos**
```bash
sudo -u postgres pg_restore -Fc -d almacen_db almacen_db.backup
```

**Paso 4: Configurar variables de entorno**
```bash
cp .env /opt/almacen-backend/.env
nano /opt/almacen-backend/.env  # Editar según sea necesario
```

**Paso 5: Crear servicio systemd**
```bash
sudo nano /etc/systemd/system/almacen-backend.service
```

Contenido:
```ini
[Unit]
Description=Backend Almacén SEDH
After=network.target postgresql.service

[Service]
Type=simple
User=almacen
WorkingDirectory=/opt/almacen-backend
Environment="PATH=/opt/almacen-backend/venv/bin"
ExecStart=/opt/almacen-backend/venv/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8081
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Paso 6: Iniciar servicio**
```bash
sudo systemctl daemon-reload
sudo systemctl enable almacen-backend
sudo systemctl start almacen-backend
```

## Seguridad

- Este backup contiene informacion sensible (variables de entorno, base de datos)
- Mantener en lugar seguro
- No compartir publicamente
- Considerar encriptacion adicional

## Informacion del Sistema

- **Backend:** Python 3.12 FastAPI
- **BD:** PostgreSQL
- **Servidor Web:** Uvicorn
- **OS:** Linux (Ubuntu 24.04)
- **Puerto:** 8081
- **Certificados:** SSL/TLS (si aplica)

## Verificacion post-restauracion

1. Acceder a http://localhost:8081/dashboard
2. Verificar login funcione
3. Verificar API endpoints: http://localhost:8081/api
4. Revisar logs: journalctl -u almacen-backend -f

## Soporte

En caso de problemas:
1. Revisar logs: journalctl -u almacen-backend
2. Verificar base de datos: psql -U usuario -d almacen_db
3. Verificar puertos: netstat -tlnp | grep 8081
4. Verificar configuracion .env

---
**Backup automatico generado**
"""
    
    with open(backup_dir / "README.md", "w") as f:
        f.write(readme_content)
    
    # 6. Crear ZIP final
    print("\n5. Creando archivo ZIP comprimido...")
    archive_name = f"backup_{backup_date}"
    
    shutil.make_archive(
        archive_name,
        "zip",
        ".",
        backup_dir.name
    )
    
    zip_file = f"{archive_name}.zip"
    zip_size = os.path.getsize(zip_file) / (1024*1024)
    
    # 7. Mostrar resumen
    print("\n" + "=" * 70)
    print("OK BACKUP COMPLETADO EXITOSAMENTE")
    print("=" * 70)
    
    print(f"\nArchivo: {zip_file}")
    print(f"Tamaño: {zip_size:.2f} MB")
    print(f"Ubicacion: {os.path.abspath(zip_file)}")
    
    print(f"\nArchivos incluidos:")
    for item in backup_dir.iterdir():
        if item.is_file():
            size = os.path.getsize(item) / 1024
            print(f"   OK {item.name} ({size:.1f} KB)")
        else:
            files_count = sum(1 for _ in item.rglob("*") if _.is_file())
            print(f"   OK {item.name}/ ({files_count} archivos)")
    
    print(f"\nRecomendaciones:")
    print(f"   1. Guarda este archivo en un lugar seguro")
    print(f"   2. Considera hacer copias adicionales")
    print(f"   3. Lee README.md para instrucciones de restauracion")
    print(f"   4. Verifica que el backup contiene lo necesario")
    
    sftp.close()
    
finally:
    client.close()
