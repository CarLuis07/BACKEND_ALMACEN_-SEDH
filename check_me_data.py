#!/usr/bin/env python3
"""
Script para verificar qué devuelve la consulta de obtener_info_empleado
"""
import sys
sys.path.insert(0, '/opt/almacen-backend')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Conexión
engine = create_engine('postgresql://postgres:Admin123@localhost:5432/almacen_db')
Session = sessionmaker(bind=engine)

email = 'humberto.zelaya@sedh.gob.hn'

print(f"🔍 Verificando datos para: {email}\n")

with Session() as db:
    # Consulta actual (la que falla)
    print("📋 Consulta ACTUAL (con LEFT JOIN):")
    row = db.execute(
        text("""
            SELECT 
            er.emailinstitucional as email,
            e.nombre,
            r.nomrol as rol,
            d.nomdependencia as dependencia
            FROM acceso.empleados_roles er
            JOIN acceso.roles r ON r.idrol = er.idrol
            LEFT JOIN usuarios.empleados e ON e.emailinstitucional = er.emailinstitucional
            LEFT JOIN usuarios.dependencias d ON d.iddependencia = e.iddependencia
            WHERE LOWER(TRIM(er.emailinstitucional)) = LOWER(TRIM(:email))
            AND COALESCE(er.actlaboralmente, FALSE) = TRUE
            LIMIT 1
        """),
        {"email": email}
    ).mappings().first()
    
    if row:
        print(f"  ✅ Resultado encontrado:")
        print(f"     Email: {row['email']}")
        print(f"     Nombre: {row['nombre']}")
        print(f"     Rol: {row['rol']}")
        print(f"     Dependencia: {row['dependencia']}")
    else:
        print(f"  ❌ No se encontró resultado")
    
    # Ver qué hay en empleados_roles directamente
    print("\n📋 Datos en acceso.empleados_roles:")
    er_row = db.execute(
        text("""
            SELECT emailinstitucional, idrol, actlaboralmente
            FROM acceso.empleados_roles
            WHERE LOWER(TRIM(emailinstitucional)) = LOWER(TRIM(:email))
        """),
        {"email": email}
    ).mappings().first()
    
    if er_row:
        print(f"  ✅ Email: {er_row['emailinstitucional']}")
        print(f"     IdRol: {er_row['idrol']}")
        print(f"     ActLaboralmente: {er_row['actlaboralmente']}")
    else:
        print(f"  ❌ No encontrado en empleados_roles")
    
    # Ver qué hay en usuarios.empleados
    print("\n📋 Datos en usuarios.empleados:")
    e_row = db.execute(
        text("""
            SELECT emailinstitucional, nombre, iddependencia
            FROM usuarios.empleados
            WHERE LOWER(TRIM(emailinstitucional)) = LOWER(TRIM(:email))
        """),
        {"email": email}
    ).mappings().first()
    
    if e_row:
        print(f"  ✅ Email: {e_row['emailinstitucional']}")
        print(f"     Nombre: {e_row['nombre']}")
        print(f"     IdDependencia: {e_row['iddependencia']}")
    else:
        print(f"  ❌ No encontrado en usuarios.empleados")

print("\n✅ Verificación completada")
