#!/usr/bin/env python3
"""
Script para crear datos maestros y configurar usuario Humberto
"""
import sys
import os
sys.path.insert(0, '/opt/almacen-backend')

from app.core.database import engine
from app.models.accesos.rol import Rol
from app.models.usuarios.dependencia import Dependencia
from app.models.usuarios.empleado import Empleado
from app.models.accesos.empleado_rol import EmpleadoRol
from sqlalchemy.orm import Session
from sqlalchemy import text
from uuid import uuid4
from datetime import date
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

print("🔧 Configurando datos maestros del sistema...\n")

with Session(engine) as session:
    # 1. Crear Roles
    print("📋 Creando Roles...")
    roles_data = [
        {'nombre': 'Administrador', 'desc': 'Acceso total al sistema'},
        {'nombre': 'Jefe de Materiales', 'desc': 'Gestión de materiales y requisiciones'},
        {'nombre': 'Empleado Almacén', 'desc': 'Personal del almacén'},
        {'nombre': 'Empleado', 'desc': 'Empleado general'},
        {'nombre': 'Jefe Inmediato', 'desc': 'Jefe de departamento'},
    ]
    
    roles_ids = {}
    for role_data in roles_data:
        try:
            # Verificar si ya existe
            existing = session.query(Rol).filter(Rol.NomRol == role_data['nombre']).first()
            if not existing:
                rol = Rol(
                    IdRol=str(uuid4()),
                    NomRol=role_data['nombre'],
                    CreadoEn=date.today(),
                    CreadoPor='Sistema'
                )
                session.add(rol)
                roles_ids[role_data['nombre']] = rol.IdRol
                print(f"  ✅ {role_data['nombre']} (creado)")
            else:
                roles_ids[role_data['nombre']] = existing.IdRol
                print(f"  ℹ️ {role_data['nombre']} (ya existe)")
        except Exception as e:
            print(f"  ⚠️ {role_data['nombre']}: {str(e)}")
    
    session.flush()
    
    # 2. Crear Dependencias
    print("\n🏢 Creando Dependencias...")
    dependencias_data = [
        {'nombre': 'Dirección General', 'sigla': 'DIR'},
        {'nombre': 'Departamento de Recursos Humanos', 'sigla': 'RRHH'},
        {'nombre': 'Departamento de Almacén', 'sigla': 'ALM'},
        {'nombre': 'Departamento de Logística', 'sigla': 'LOG'},
        {'nombre': 'Departamento Administrativo', 'sigla': 'ADM'},
    ]
    
    deps_ids = {}
    for dep_data in dependencias_data:
        try:
            # Verificar si ya existe
            existing = session.query(Dependencia).filter(
                Dependencia.NomDependencia == dep_data['nombre']
            ).first()
            if not existing:
                dep = Dependencia(
                    IdDependencia=str(uuid4()),
                    NomDependencia=dep_data['nombre'],
                    CreadoEn=date.today(),
                    CreadoPor='Sistema'
                )
                session.add(dep)
                deps_ids[dep_data['nombre']] = dep.IdDependencia
                print(f"  ✅ {dep_data['nombre']} (creado)")
            else:
                deps_ids[dep_data['nombre']] = existing.IdDependencia
                print(f"  ℹ️ {dep_data['nombre']} (ya existe)")
        except Exception as e:
            print(f"  ⚠️ {dep_data['nombre']}: {str(e)}")
    
    session.flush()
    
    # 3. Actualizar contraseña de Humberto y crear EmpleadoRol
    print("\n👤 Configurando usuario Humberto...")
    try:
        humberto = session.query(Empleado).filter(
            Empleado.EmailInstitucional == 'humberto.zelaya@sedh.gob.hn'
        ).first()
        
        if humberto:
            # Hashear la nueva contraseña
            hashed_password = pwd_context.hash('Derechos25')
            
            # Verificar si ya tiene EmpleadoRol
            emp_rol = session.query(EmpleadoRol).filter(
                EmpleadoRol.EmailInstitucional == 'humberto.zelaya@sedh.gob.hn'
            ).first()
            
            if not emp_rol:
                # Crear EmpleadoRol con contraseña
                admin_role = session.query(Rol).filter(
                    Rol.NomRol == 'Administrador'
                ).first()
                
                if admin_role:
                    emp_rol = EmpleadoRol(
                        IdEmpleadoRol=str(uuid4()),
                        EmailInstitucional='humberto.zelaya@sedh.gob.hn',
                        IdRol=admin_role.IdRol,
                        Contrasena=hashed_password,
                        ActLaboralmente=True,
                        CreadoEn=date.today(),
                        CreadoPor='Sistema'
                    )
                    session.add(emp_rol)
                    print(f"  ✅ EmpleadoRol creado con rol: Administrador")
            else:
                # Actualizar contraseña existente
                emp_rol.Contrasena = hashed_password
                print(f"  ✅ Contraseña actualizada")
            
            print(f"  ✅ Usuario Humberto configurado:")
            print(f"     - Email: {humberto.EmailInstitucional}")
            print(f"     - Nombre: {humberto.Nombre}")
        else:
            print(f"  ❌ Usuario Humberto no encontrado")
    except Exception as e:
        print(f"  ⚠️ Error al configurar Humberto: {str(e)}")
        import traceback
        traceback.print_exc()
    
    session.commit()

print("\n✅ Datos maestros configurados exitosamente!")

# Verificar
print("\n📊 Verificando datos creados:")
with Session(engine) as session:
    roles_count = session.query(Rol).count()
    deps_count = session.query(Dependencia).count()
    emp_roles = session.query(EmpleadoRol).filter(
        EmpleadoRol.EmailInstitucional == 'humberto.zelaya@sedh.gob.hn'
    ).first()
    
    print(f"  ✅ Roles creados: {roles_count}")
    print(f"  ✅ Dependencias creadas: {deps_count}")
    if emp_roles:
        print(f"  ✅ Humberto con credenciales configuradas")

print("\n🎉 ¡Sistema listo para usar!")
print("   URL: http://192.168.180.164:8081/")
print("   Usuario: humberto.zelaya@sedh.gob.hn")
print("   Contraseña: Derechos25")
