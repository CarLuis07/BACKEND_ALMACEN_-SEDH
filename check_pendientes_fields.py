#!/usr/bin/env python3
"""Script para verificar qué campos devuelve la función requisiciones_pendientes_jefe"""

import sys
import os

# Agregar el directorio app al path para importar los módulos
sys.path.insert(0, '/opt/almacen-backend')

from app.core.database import SessionLocal
from sqlalchemy import text

def check_requisiciones_pendientes():
    db = SessionLocal()
    try:
        # Ejecutar la función con un email de ejemplo
        email = 'jefsermat@sedh.gob.hn'  # Usar un email válido de jefe
        
        query = text("""
            SELECT *
            FROM requisiciones.requisiciones_pendientes_jefe(:p_email)
            LIMIT 1
        """)
        
        result = db.execute(query, {"p_email": email}).mappings().first()
        
        if result:
            print("Campos devueltos por la función:")
            print("-" * 50)
            for key, value in dict(result).items():
                print(f"{key}: {type(value).__name__} = {value if not isinstance(value, (list, dict)) else '...'}")
        else:
            print("No se encontraron requisiciones pendientes")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_requisiciones_pendientes()
