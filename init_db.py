#!/usr/bin/env python3
"""Script para crear las tablas de base de datos en el servidor"""

import sys
import os

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Importar Base y engine
    from app.core.database import Base, engine
    from sqlalchemy import text
    
    # Crear los schemas necesarios
    print("🔄 Creando schemas...")
    with engine.connect() as conn:
        # Habilitar extensión UUID
        conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
        # Crear schemas
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS usuarios"))
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS acceso"))
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS productos"))
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS requisiciones"))
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS movimientos"))
        conn.commit()
    print("✅ Schemas creados")
    
    # Importar TODOS los modelos para que SQLAlchemy los registre
    from app.models.usuarios.empleado import Empleado
    from app.models.usuarios.dependencia import Dependencia
    from app.models.accesos.rol import Rol
    from app.models.accesos.empleado_rol import EmpleadoRol
    from app.models.productos.producto import Producto
    from app.models.productos.categoria import Categoria
    from app.models.productos.unidad_medida import UnidadMedida
    from app.models.requisiciones.requisicion import Requisicion
    from app.models.requisiciones.detalle_requisicion import DetalleRequisicion
    from app.models.requisiciones.historial_requisicion import HistorialRequisicion
    from app.models.requisiciones.estado_solicitud import EstadoSolicitud
    from app.models.requisiciones.aprobacion import Aprobacion
    from app.models.movimientos.movimiento import Movimiento
    from app.models.movimientos.tipo_movimiento import TipoMovimiento
    
    print("🔄 Creando tablas de base de datos...")
    print(f"Modelos registrados: {len(Base.metadata.tables)}")
    Base.metadata.create_all(bind=engine)
    print("✅ Tablas de base de datos creadas exitosamente")
    
except Exception as e:
    print(f"❌ Error al crear tablas: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
