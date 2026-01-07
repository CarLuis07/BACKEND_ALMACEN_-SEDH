import sys
sys.path.insert(0, '/opt/almacen-backend')
from sqlalchemy import create_engine, text

engine = create_engine('postgresql://postgres:Admin123@localhost:5432/almacen_db')

with engine.connect() as conn:
    # Ver la definición de la función SQL
    result = conn.execute(text("""
        SELECT pg_get_functiondef(oid) 
        FROM pg_proc 
        WHERE proname = 'responder_requisicion_jefe_materiales'
    """)).fetchone()
    
    if result:
        print("Definición de responder_requisicion_jefe_materiales:")
        print("=" * 80)
        print(result[0])
