import sys
sys.path.insert(0, '/opt/almacen-backend')
from sqlalchemy import create_engine, text

engine = create_engine('postgresql://postgres:Admin123@localhost:5432/almacen_db')

with engine.connect() as conn:
    # Ver qué devuelve la función SQL para jefe materiales
    result = conn.execute(text("""
        SELECT * FROM requisiciones.requisiciones_pendientes_jefe_materiales('escarleth.nunez@sedh.gob.hn')
    """)).fetchall()
    
    print("=" * 80)
    print(f"Total requisiciones devueltas por función SQL: {len(result)}")
    print("=" * 80)
    
    if result:
        # Ver columnas
        print("Columnas:", result[0]._fields if hasattr(result[0], '_fields') else 'N/A')
        print()
        
        for idx, row in enumerate(result):
            print(f"#{idx + 1}: {row[1] if len(row) > 1 else 'N/A'}")  # codRequisicion
    
    print("\n" + "=" * 80)
    # Ver estado de aprobaciones de JefSerMat para UIT-001-2026
    aprob = conn.execute(text("""
        SELECT r.codrequisicion, a.rol, a.estadoaprobacion, a.fecaprobacion
        FROM requisiciones.requisiciones r
        LEFT JOIN requisiciones.aprobaciones a ON a.idrequisicion = r.idrequisicion
        WHERE r.codrequisicion = 'UIT-001-2026'
        ORDER BY a.fecaprobacion DESC NULLS LAST
    """)).fetchall()
    
    print("Aprobaciones de UIT-001-2026:")
    print("=" * 80)
    for a in aprob:
        print(f"Código: {a[0]}, Rol: {a[1]}, Estado: {a[2]}, Fecha: {a[3]}")
