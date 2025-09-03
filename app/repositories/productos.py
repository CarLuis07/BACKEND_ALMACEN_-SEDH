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
    p.gasunitario
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
    :p_creadopor
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
    raw = db.execute(text(SQL_LISTAR_CATEGORIAS_Y_UNIDADES)).scalar()
    if raw is None:
        return CatalogosProductoOut(categorias=[], unidades=[])

    if isinstance(raw, str):
        data = json.loads(raw)
    elif isinstance(raw, Mapping):
        data = dict(raw)
    else:
        # Fallback en caso de tipo no esperado
        data = json.loads(str(raw))

    categorias = [
        {"idcategoria": c.get("IdCategoria"), "codobjeto": c.get("CodObjeto")}
        for c in data.get("categorias", [])
    ]
    unidades = [
        {"idunidadmedida": u.get("IdUnidadMedida"), "nomunidad": u.get("NomUnidad")}
        for u in data.get("unidades", [])
    ]

    return CatalogosProductoOut(
        categorias=[CategoriaRefOut(**c) for c in categorias],
        unidades=[UnidadMedidaOut(**u) for u in unidades],
    )

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
    }
    try:
        res = db.execute(text(SQL_CREAR_PRODUCTO), params).scalar()
        db.commit()  
    except Exception:
        db.rollback()
        raise
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
    try:
        res = db.execute(text(SQL_CREAR_CATEGORIA), params).scalar()
        db.commit()
    except Exception:
        db.rollback()
        raise
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
    try:
        res = db.execute(text(SQL_EDITAR_CATEGORIA), params).scalar()
        db.commit()
    except Exception:
        db.rollback()
        raise
    return bool(res) if res is not None else True

def buscar_categoria(db: Session, codobjeto: int) -> List[CategoriaOut]:
    res = db.execute(text(SQL_BUSCAR_CATEGORIA), {"p_codobjeto": codobjeto}).mappings().all()
    return [CategoriaOut(**_normalize_row(r)) for r in res]