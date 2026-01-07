#!/usr/bin/env python3
"""Script para verificar el estado de la requisición UIT-001-2026"""

import sys
sys.path.insert(0, '/opt/almacen-backend')

from app.core.database import SessionLocal
from sqlalchemy import text

def verificar_requisicion():
    db = SessionLocal()
    try:
        # Ver el estado actual de la requisición
        query = text("""
            SELECT 
                codrequisicion,
                estgeneral,
                fecsolicitud
            FROM requisiciones.requisiciones
            WHERE codrequisicion = 'UIT-001-2026'
        """)
        
        result = db.execute(query).mappings().first()
        
        if result:
            print("Estado de UIT-001-2026:")
            print("-" * 50)
            for key, value in dict(result).items():
                print(f"{key}: {value}")
            print()
            
            # Ver qué devuelve la función para el jefe de materiales
            email_jefe = 'escarleth.ortiz@sedh.gob.hn'
            query2 = text("""
                SELECT codrequisicion, estgeneral
                FROM requisiciones.requisiciones_pendientes_jefe_materiales(:p_email)
            """)
            
            results = db.execute(query2, {"p_email": email_jefe}).mappings().all()
            print(f"\nRequisiciones que ve {email_jefe}:")
            print("-" * 50)
            for r in results:
                print(f"  - {r['codrequisicion']}: {r.get('estgeneral', 'N/A')}")
        else:
            print("No se encontró la requisición UIT-001-2026")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    verificar_requisicion()
