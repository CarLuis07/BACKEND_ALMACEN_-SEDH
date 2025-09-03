# Backend Almacén SEDH

Monolito modular FastAPI (sin Alembic; DDL gestionado en PostgreSQL).

## Módulos activos
- usuarios (Empleados)
- accesos (login via SP acceso.LoginUsuario)

## Estructura
```
app/
  core/ (config, database, security)
  api/ (routers)
  models/
    accesos/
    usuarios/
  schemas/
  repositories/
```

## Variables .env
SECRET_KEY=...
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=...
DB_NAME=almacen_db
ENV=dev

## Entorno
python -m venv .venv

source .venv/Scripts/activate  
python -m pip install --upgrade pip
pip install -r requirements.txt

## Ejecutar
python -m uvicorn app.main:app --reload  
 (si reload falla en Git Bash: python -m uvicorn app.main:app)

## Endpoints
GET  /api/v1/health/db
POST /api/v1/accesos/login  { "email": "...", "password": "..." }
POST /api/v1/usuarios/      crear empleado
GET  /api/v1/usuarios/
GET  /api/v1/usuarios/{email}

## Notas
- No se crean tablas desde la app.
- Login delega la validación al SP. Si el SP devuelve error se responde 401.



# FUNCIONAMIENTO DE ESTA ARQUITECTURA (MONOLITICA MODULAR)

- #### Configuración global: 
app.core.config.settings carga variables (.env) y expone configuración.
* #### DB / ORM: 
app.core.database.Base, engine, SessionLocal, get_db preparan SQLAlchemy; los modelos heredan de Base.
* #### Modelos (persistencia): ej. 
app.models.usuarios.empleado.Empleado define tablas/columnas.
* #### Schemas (validación / I/O): ej. 
app.schemas.usuarios.empleado.EmpleadoCreate, EmpleadoRead definen payload de entrada y salida (aislan el modelo).
* #### Repositorio (acceso a datos / SP): ej. 
app.repositories.accesos.login_empleado encapsula llamadas SQL / Stored Procedures.
* #### Seguridad / utilidades: ej. 
app.core.security.create_access_token.
* #### Routers (capa API): ej. 
app.api.usuarios.router.crear_empleado orquesta: recibe request -> valida con schema -> usa sesión DB (get_db) -> interactúa con modelo / repositorio -> retorna schema de salida.
* #### App principal: 
app.main.app monta routers con prefijos y health checks (ej. app.core.database.test_db_connection).