import sys
import os
# Configurar PYTHONPATH automáticamente
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
from datetime import date

from app.core.database import get_db
from app.core.security import get_current_user

router = APIRouter()

@router.get("/", summary="Listado de movimientos")
async def listar_movimientos(
    fecha_inicio: Optional[date] = Query(None, description="Fecha inicial del rango"),
    fecha_fin: Optional[date] = Query(None, description="Fecha final del rango"),
    tipo_movimiento: Optional[str] = Query(None, description="Tipo de movimiento"),
    id_producto: Optional[str] = Query(None, description="ID del producto"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Listar todos los movimientos de inventario con filtros opcionales.
    Disponible para roles: EmpAlmacen, Auditor, Administrador
    """
    try:
        # Construir query base - SIN tabla Tipos_Movimientos que no existe
        query = """
        SELECT 
            m.idmovimiento,
            m.fecmovimiento,
            'Movimiento' as nomtipomovimiento,
            p.nomproducto,
            p.codobjetounico,
            c.nomcategoria,
            dr.cantsolicitada,
            dr.cantentregada,
            r.codrequisicion,
            m.creadopor,
            m.creadoen
        FROM movimientos.movimientos m
        LEFT JOIN productos.productos p ON m.idproducto = p.idproducto
        LEFT JOIN productos.categorias c ON m.idcategoria = c.idcategoria
        LEFT JOIN requisiciones.requisiciones r ON m.idrequisicion = r.idrequisicion
        LEFT JOIN requisiciones.detalle_requisicion dr ON dr.idrequisicion = m.idrequisicion 
            AND dr.idproducto = m.idproducto
        WHERE 1=1
        """
        
        params = {}
        
        # Aplicar filtros
        if fecha_inicio:
            query += " AND m.fecmovimiento >= :fecha_inicio"
            params['fecha_inicio'] = fecha_inicio
            
        if fecha_fin:
            query += " AND m.fecmovimiento <= :fecha_fin"
            params['fecha_fin'] = fecha_fin
            
        # Comentado porque la tabla Tipos_Movimientos no existe
        # if tipo_movimiento:
        #     query += " AND tm.nomtipomovimiento ILIKE :tipo_movimiento"
        #     params['tipo_movimiento'] = f"%{tipo_movimiento}%"
            
        if id_producto:
            query += " AND m.idproducto = :id_producto"
            params['id_producto'] = id_producto
        
        query += " ORDER BY m.fecmovimiento DESC, m.creadoen DESC"
        
        result = db.execute(text(query), params)
        
        movimientos = []
        for row in result.mappings():
            movimientos.append({
                'idMovimiento': str(row['idmovimiento']) if row['idmovimiento'] else None,
                'fechaMovimiento': row['fecmovimiento'].isoformat() if row['fecmovimiento'] else None,
                'tipoMovimiento': row['nomtipomovimiento'] or 'N/A',
                'producto': row['nomproducto'] or 'N/A',
                'codigoProducto': row['codobjetounico'] or 'N/A',
                'categoria': row['nomcategoria'] or 'N/A',
                'cantidadSolicitada': float(row['cantsolicitada']) if row['cantsolicitada'] else 0,
                'cantidadEntregada': float(row['cantentregada']) if row['cantentregada'] else 0,
                'requisicion': row['codrequisicion'] or 'N/A',
                'creadoPor': row['creadopor'] or 'Sistema',
                'creadoEn': row['creadoen'].isoformat() if row['creadoen'] else None
            })
        
        return movimientos
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener movimientos: {str(e)}")

@router.get("/resumen", summary="Resumen de movimientos")
async def resumen_movimientos(
    mes: Optional[int] = Query(None, description="Mes (1-12)"),
    anio: Optional[int] = Query(None, description="Año"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Obtener resumen estadístico de movimientos.
    Para reportes y auditoría.
    """
    try:
        query = """
        SELECT 
            COUNT(*) as total_movimientos,
            COUNT(DISTINCT m.idproducto) as productos_movidos,
            COUNT(DISTINCT m.idrequisicion) as requisiciones_procesadas,
            COUNT(DISTINCT m.creadopor) as usuarios_activos
        FROM movimientos.movimientos m
        WHERE 1=1
        """
        
        params = {}
        
        if mes and anio:
            query += " AND EXTRACT(MONTH FROM m.fecmovimiento) = :mes"
            query += " AND EXTRACT(YEAR FROM m.fecmovimiento) = :anio"
            params['mes'] = mes
            params['anio'] = anio
        elif anio:
            query += " AND EXTRACT(YEAR FROM m.fecmovimiento) = :anio"
            params['anio'] = anio
        
        result = db.execute(text(query), params).mappings().first()
        
        return {
            'totalMovimientos': result['total_movimientos'] or 0,
            'productosMovidos': result['productos_movidos'] or 0,
            'requisicionesProcesadas': result['requisiciones_procesadas'] or 0,
            'usuariosActivos': result['usuarios_activos'] or 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener resumen: {str(e)}")

