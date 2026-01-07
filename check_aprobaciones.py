import sys
sys.path.insert(0, '/opt/almacen-backend')
from sqlalchemy import create_engine, text

engine = create_engine('postgresql://postgres:Admin123@localhost:5432/almacen_db')

with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT codrequisicion, rol, estadoaprobacion, fecaprobacion 
        FROM requisiciones.aprobaciones a 
        JOIN requisiciones.requisiciones r ON r.idrequisicion=a.idrequisicion 
        WHERE codrequisicion='UIT-001-2026' 
        ORDER BY fecaprobacion DESC NULLS LAST
    """)).fetchall()
    
    print("Aprobaciones de UIT-001-2026:")
    print("=" * 80)
    if not result:
        print("NO HAY APROBACIONES REGISTRADAS (excepto JefInmediato)")
    for r in result:
        print(f'{r[0]} | Rol: {r[1]} | Estado: {r[2]} | Fecha: {r[3]}')
