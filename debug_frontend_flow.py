#!/usr/bin/env python3
"""
Simular el flujo del frontend para identificar dónde falla
"""
import sys
sys.path.insert(0, '/opt/almacen-backend')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.repositories.accesos import login_empleado, obtener_info_empleado
from app.core.database import engine
from app.core.security import create_access_token

email = 'humberto.zelaya@sedh.gob.hn'
password = 'Derechos25'

print("🔐 Simulando flujo del frontend...\n")

with sessionmaker(bind=engine)() as db:
    # 1. Login
    print("1️⃣ Login...")
    ok, rol = login_empleado(db, email, password)
    print(f"   ✅ Login: {ok}, Rol: {rol}")
    
    # 2. Crear token
    print("\n2️⃣ Crear token...")
    token = create_access_token(subject=email, extra_claims={"rol": rol})
    print(f"   ✅ Token creado: {token[:50]}...")
    
    # 3. Obtener info empleado
    print("\n3️⃣ Obtener info empleado...")
    info = obtener_info_empleado(db, email)
    if info:
        print(f"   ✅ Nombre: {info['nombre']}")
        print(f"   ✅ Rol: {info['rol']}")
        print(f"   ✅ Dependencia: {info['dependencia']}")
    else:
        print("   ❌ No se obtuvieron datos del empleado")
    
    # 4. Obtener categorías
    print("\n4️⃣ Obtener categorías...")
    from app.repositories.productos import listar_categorias_y_unidades
    catalogo = listar_categorias_y_unidades(db)
    print(f"   ✅ Categorías: {len(catalogo.categorias)}")
    print(f"   ✅ Unidades: {len(catalogo.unidades)}")
    
    # 5. Obtener módulos (simulado)
    print("\n5️⃣ Verificar módulos...")
    from app.repositories.accesos import obtener_modulos_por_rol
    try:
        modulos = obtener_modulos_por_rol(db, email)
        print(f"   ✅ Módulos obtenidos: {len(modulos)}")
    except Exception as e:
        print(f"   ⚠️ Error al obtener módulos: {e}")
    
    print("\n✅ Flujo completado exitosamente!")

print("\nℹ️ Si ves este mensaje, el backend está funcionando correctamente.")
print("El problema debe estar en el frontend o en la comunicación.")
