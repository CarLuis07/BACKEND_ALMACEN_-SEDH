#!/usr/bin/env python3
"""Test obtener_info_empleado"""
import sys
sys.path.insert(0, '/opt/almacen-backend')

from app.repositories.accesos import obtener_info_empleado
from app.core.database import engine
from sqlalchemy.orm import Session

db = Session(engine)
result = obtener_info_empleado(db, "humberto.zelaya@sedh.gob.hn")
print("Resultado obtener_info_empleado:")
print(result)
db.close()
