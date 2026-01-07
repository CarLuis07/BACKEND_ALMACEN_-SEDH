import sys
sys.path.insert(0, '/opt/almacen-backend')
from sqlalchemy import create_engine, text

engine = create_engine('postgresql://postgres:Admin123@localhost:5432/almacen_db')

with engine.connect() as conn:
    # Ver estado de UIT-001-2026
    result = conn.execute(text("""
        SELECT r.codrequisicion, r.estgeneral, 
               a.rol, a.estadoaprobacion, a.fecaprobacion
        FROM requisiciones.requisiciones r
        LEFT JOIN requisiciones.aprobaciones a ON a.idrequisicion = r.idrequisicion
        WHERE r.codrequisicion = 'UIT-001-2026'
        ORDER BY a.fecaprobacion DESC NULLS LAST
    """)).fetchall()
    
    print("=" * 80)
    print("Estado de UIT-001-2026:")
    print("=" * 80)
    for row in result:
        print(f"Código: {row[0]}")
        print(f"EstGeneral: {row[1]}")
        print(f"Rol: {row[2]}")
        print(f"Estado Aprobación: {row[3]}")
        print(f"Fecha: {row[4]}")
        print("-" * 80)
