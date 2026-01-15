# BACKUP DEL PROYECTO ALMACÉN

Fecha: 2026-01-15 08:09:21

## Contenido del backup:

1. **almacen-backend.tar.gz** - Código fuente completo del backend
   - Directorio: /opt/almacen-backend
   - Incluye: app/, venv/, requirements.txt, etc.

2. **almacen_db.backup** - Base de datos PostgreSQL (formato custom)
   - Nombre de base de datos: almacen_db
   - Para restaurar: pg_restore -Fc -d almacen_db almacen_db.backup

3. **postman/** - Colecciones de Postman (si existen)

## Servidor de origen:
- IP: 192.168.180.164
- Usuario: administrador

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
