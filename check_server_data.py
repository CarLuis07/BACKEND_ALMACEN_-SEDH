import subprocess
import sys

sys.path.insert(0, '/opt/almacen-backend')
from app.core.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    roles = conn.execute(text('SELECT COUNT(*) FROM acceso."Roles"')).scalar()
    productos = conn.execute(text('SELECT COUNT(*) FROM productos."Productos"')).scalar()
    dependencias = conn.execute(text('SELECT COUNT(*) FROM usuarios."Dependencias"')).scalar()
    print(f'Roles: {roles}')
    print(f'Productos: {productos}')
    print(f'Dependencias: {dependencias}')
