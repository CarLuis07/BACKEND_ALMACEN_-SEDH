#!/usr/bin/env python3
"""
Script para verificar y corregir el rol de Humberto
"""
import sys
sys.path.insert(0, '/opt/almacen-backend')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Conexión
engine = create_engine('postgresql://postgres:Admin123@localhost:5432/almacen_db')
Session = sessionmaker(bind=engine)

print("🔍 Verificando roles en el sistema\n")

with Session() as db:
    # Ver todos los roles
    print("📋 Roles disponibles:")
    roles = db.execute(
        text("SELECT idrol, nomrol FROM acceso.roles ORDER BY nomrol")
    ).mappings().all()
    
    for rol in roles:
        print(f"  {rol['nomrol']:30s} | {rol['idrol']}")
    
    # Ver el rol actual de Humberto
    print("\n📋 Rol actual de Humberto:")
    current = db.execute(
        text("""
            SELECT er.emailinstitucional, r.nomrol, r.idrol as id_rol_actual
            FROM acceso.empleados_roles er
            JOIN acceso.roles r ON r.idrol = er.idrol
            WHERE er.emailinstitucional = 'humberto.zelaya@sedh.gob.hn'
        """)
    ).mappings().first()
    
    if current:
        print(f"  Email: {current['emailinstitucional']}")
        print(f"  Rol Actual: {current['nomrol']}")
        print(f"  ID: {current['id_rol_actual']}")
        
        # Encontrar el ID del rol Administrador
        admin_rol = db.execute(
            text("SELECT idrol FROM acceso.roles WHERE nomrol = 'Administrador'")
        ).mappings().first()
        
        if admin_rol and current['nomrol'] != 'Administrador':
            print(f"\n🔧 Actualizando a Administrador...")
            db.execute(
                text("""
                    UPDATE acceso.empleados_roles
                    SET idrol = :admin_id
                    WHERE emailinstitucional = 'humberto.zelaya@sedh.gob.hn'
                """),
                {"admin_id": admin_rol['idrol']}
            )
            db.commit()
            print(f"  ✅ Rol actualizado a: Administrador")
            print(f"     Nuevo ID: {admin_rol['idrol']}")
        elif current['nomrol'] == 'Administrador':
            print(f"\n  ℹ️ Ya tiene el rol Administrador")
    else:
        print("  ❌ No se encontró a Humberto en empleados_roles")

print("\n✅ Verificación completada")
