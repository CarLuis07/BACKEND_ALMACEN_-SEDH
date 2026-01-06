from typing import List, Dict, Any, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session
import json
from typing import Mapping
from uuid import UUID

from app.schemas.productos.schemas import CategoriaOut, ProductoPorCategoriaOut, ProductoOut, CatalogosProductoOut, CategoriaRefOut, UnidadMedidaOut, ProductoCreateIn
from app.schemas.productos.schemas import CategoriaCreateIn  # nuevo

SQL_LISTAR_CATEGORIAS = """
SELECT codobjeto, nomcategoria, descategoria, imagen
FROM productos.categorias
ORDER BY codobjeto
"""

SQL_PRODUCTOS_POR_CATEGORIA = """
SELECT * FROM productos.VerProductosPorCategoria(:p_codobjeto)
"""

SQL_LISTAR_PRODUCTOS = """
SELECT 
    p.idproducto,
    p.nomproducto,
    c.nomcategoria,
    p.descproducto,
    p.canstock,
    p.gasunitario,
    COALESCE(p.codobjetounico, '') as "CodObjetoUnico",
    COALESCE(p.codobjetounico, '') as codobjetunico,
    p.Facturas AS facturas,
    p.OrdenesCompra AS ordenescompra,
    p.fecvencimiento
FROM productos.productos p
JOIN productos.categorias c ON p.idcategoria = c.idcategoria
ORDER BY c.nomcategoria, p.nomproducto
"""

SQL_BUSCAR_PRODUCTOS = """
SELECT * FROM productos.BuscarProductos(:p_nomproducto, :p_codobjeto)
"""

SQL_BUSCAR_CATEGORIA = """
SELECT * FROM productos.BuscarCategoria(:p_codobjeto)
"""

SQL_LISTAR_CATEGORIAS_Y_UNIDADES = """
SELECT productos.ListarCategoriasYUnidades() AS data
"""

SQL_CREAR_PRODUCTO = """
SELECT productos.CrearProducto(
    :p_idcategoria,
    :p_fecingreso,
    :p_nomproducto,
    :p_descproducto,
    :p_canstock,
    :p_proveedor,
    :p_limstockbajo,
    :p_fecvencimiento,
    :p_idunidadmedida,
    :p_gasunitario,
    :p_gastotal,
    :p_creadopor,
    :p_facturas,
    :p_ordenescompra
    ) AS idproducto
"""

SQL_CREAR_CATEGORIA = """
SELECT productos.CrearCategoria(
    :p_codobjeto,
    :p_nomcategoria,
    :p_descategoria,
    :p_creadopor,
    :p_imagen
) AS idcategoria
"""

# Nuevo: SQL editar categoría
SQL_EDITAR_CATEGORIA = """
SELECT productos.EditarCategoria(
    :p_idcategoria,
    :p_actualizadopor,
    :p_codobjeto,
    :p_nomcategoria,
    :p_descategoria,
    :p_imagen
    ) AS ok
"""

def _normalize_row(row: Dict[str, Any]) -> Dict[str, Any]:
    d = dict(row)
    if "imagen" in d and d["imagen"] is not None and not isinstance(d["imagen"], (bytes, bytearray)):
        try:
            d["imagen"] = bytes(d["imagen"])
        except Exception:
            pass
    return d

##USUARIOS EMPLEADOS
def listar_categorias(db: Session) -> List[CategoriaOut]:
    res = db.execute(text(SQL_LISTAR_CATEGORIAS)).mappings().all()
    return [CategoriaOut(**_normalize_row(r)) for r in res]

def ver_productos_por_categoria(db: Session, codobjeto: int) -> List[ProductoPorCategoriaOut]:
    res = db.execute(text(SQL_PRODUCTOS_POR_CATEGORIA), {"p_codobjeto": codobjeto}).mappings().all()
    return [ProductoPorCategoriaOut(**dict(r)) for r in res]

def listar_productos(db: Session) -> List[ProductoOut]:
    res = db.execute(text(SQL_LISTAR_PRODUCTOS)).mappings().all()
    return [ProductoOut(**dict(r)) for r in res]

def buscar_productos(db: Session, nomproducto: Optional[str], codobjeto: Optional[int]) -> List[ProductoOut]:
    params = {"p_nomproducto": nomproducto, "p_codobjeto": codobjeto}
    res = db.execute(text(SQL_BUSCAR_PRODUCTOS), params).mappings().all()
    return [ProductoOut(**dict(r)) for r in res]

def listar_categorias_y_unidades(db: Session) -> CatalogosProductoOut:
    """
    Obtiene categorías y unidades de medida directamente desde las tablas
    Sin depender de stored procedures que podrían no existir
    """
    try:
        # Obtener categorías directamente
        categorias_query = db.execute(text("""
            SELECT "IdCategoria" as idcategoria, "CodObjeto" as codobjeto, "NomCategoria" as nomcategoria
            FROM productos."Categorias"
            ORDER BY "CodObjeto"
        """)).mappings().all()
        
        # Obtener unidades de medida directamente
        unidades_query = db.execute(text("""
            SELECT "IdUnidadMedida" as idunidadmedida, "NomUnidad" as nomunidad
            FROM productos."Unidades_Medida"
            ORDER BY "NomUnidad"
        """)).mappings().all()
        
        categorias = [CategoriaRefOut(**dict(c)) for c in categorias_query]
        unidades = [UnidadMedidaOut(**dict(u)) for u in unidades_query]
        
        return CatalogosProductoOut(categorias=categorias, unidades=unidades)
        
    except Exception as e:
        print(f"❌ Error en listar_categorias_y_unidades: {str(e)}")
        import traceback
        traceback.print_exc()
        return CatalogosProductoOut(categorias=[], unidades=[])

##USUARIOS EMPLEADOS ALMACEN
def crear_producto(db: Session, payload: ProductoCreateIn, creado_por: str) -> Optional[UUID]:
    params = {
        "p_idcategoria": str(payload.idcategoria),
        "p_fecingreso": payload.fecingreso,
        "p_nomproducto": payload.nomproducto,
        "p_descproducto": payload.descproducto,
        "p_canstock": payload.canstock,
        "p_proveedor": payload.proveedor,
        "p_limstockbajo": payload.limstockbajo,
        "p_fecvencimiento": payload.fecvencimiento,
        "p_idunidadmedida": str(payload.idunidadmedida),
        "p_gasunitario": payload.gasunitario,
        "p_gastotal": payload.gastotal,
        "p_creadopor": creado_por,
        "p_facturas": payload.facturas,
        "p_ordenescompra": payload.ordenescompra,
    }
    res = db.execute(text(SQL_CREAR_PRODUCTO), params).scalar()
    db.flush()  # Asegurar que la transacción está pending
    try:
        return UUID(str(res)) if res is not None else None
    except Exception:
        return None

def crear_categoria(db: Session, payload: CategoriaCreateIn, creado_por: str) -> Optional[UUID]:
    params = {
        "p_codobjeto": payload.codobjeto,
        "p_nomcategoria": payload.nomcategoria,
        "p_descategoria": payload.descategoria,
        "p_creadopor": creado_por,
        "p_imagen": payload.imagen,  # None o bytes
    }
    res = db.execute(text(SQL_CREAR_CATEGORIA), params).scalar()
    db.flush()  # Asegurar que la transacción está pending
    try:
        return UUID(str(res)) if res is not None else None
    except Exception:
        return None

def editar_categoria(db: Session, idcategoria: UUID, payload, actualizado_por: str) -> bool:
    params = {
        "p_idcategoria": str(idcategoria),
        "p_actualizadopor": actualizado_por,
        "p_codobjeto": payload.codobjeto,
        "p_nomcategoria": payload.nomcategoria,
        "p_descategoria": payload.descategoria,
        "p_imagen": payload.imagen,
    }
    res = db.execute(text(SQL_EDITAR_CATEGORIA), params).scalar()
    db.flush()  # Asegurar que la transacción está pending
    return bool(res) if res is not None else True

def buscar_categoria(db: Session, codobjeto: int) -> List[CategoriaOut]:
    res = db.execute(text(SQL_BUSCAR_CATEGORIA), {"p_codobjeto": codobjeto}).mappings().all()
    return [CategoriaOut(**_normalize_row(r)) for r in res]