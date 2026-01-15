# BACKUP COMPLETO - ALMACÉN SEDH

**Fecha:** 2026-01-15 08:19:06  
**Servidor:** 192.168.180.164

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
