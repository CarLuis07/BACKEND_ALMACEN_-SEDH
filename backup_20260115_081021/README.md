# BACKUP COMPLETO - ALMACÉN SEDH

**Fecha de backup:** 2026-01-15 08:10:24

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
- **IP:** 192.168.180.164
- **Usuario:** administrador
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
