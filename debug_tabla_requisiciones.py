#!/usr/bin/env python3
"""Script para depurar el endpoint de requisiciones pendientes"""

import sys
sys.path.insert(0, '/opt/almacen-backend')

from app.core.database import SessionLocal
from sqlalchemy import text
import json

def check_estructura_tabla():
    db = SessionLocal()
    try:
        # Ver la estructura de la tabla de requisiciones
        query = text("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'requisiciones' 
            AND table_name = 'requisicion'
            ORDER BY ordinal_position;
        """)
        
        print("Estructura de la tabla requisiciones.requisicion:")
        print("-" * 60)
        for row in db.execute(query):
            print(f"{row[0]}: {row[1]}")
        
        print("\n" + "=" * 60)
        print("Requisiciones con estado PENDIENTE:")
        print("=" * 60)
        
        # Ver una requisición pendiente directamente
        query2 = text("""
            SELECT 
                r.idrequisicion,
                r.codrequisicion,
                e.nombre_empleado as solicitante,
                d.nombre_dependencia,
                r.fec_solicitud,
                r.obs_empleado,
                r.gas_total_del_pedido
            FROM requisiciones.requisicion r
            LEFT JOIN rrhh.empleado e ON r.idempleado = e.idempleado
            LEFT JOIN rrhh.dependencia d ON e.iddependencia = d.iddependencia
            WHERE r.estado_solicitud = 'PENDIENTE'
            LIMIT 1;
        """)
        
        result = db.execute(query2).mappings().first()
        if result:
            print("\nEjemplo de requisición pendiente:")
            print("-" * 60)
            for key, value in dict(result).items():
                print(f"{key}: {value}")
        else:
            print("\nNo hay requisiciones pendientes")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_estructura_tabla()
