from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.security import get_current_user
from app.core.database import get_db
from app.repositories.productos import listar_categorias, ver_productos_por_categoria, listar_productos, buscar_productos, listar_categorias_y_unidades, crear_producto, crear_categoria, editar_categoria, buscar_categoria
from app.schemas.productos.schemas import CategoriaOut, ProductoPorCategoriaOut, ProductoOut, CatalogosProductoOut, ProductoCreateIn, ProductoCreateOut, CategoriaCreateIn, CategoriaCreateOut, CategoriaUpdateIn, CategoriaUpdateOut

router = APIRouter()

##USUARIOS EMPLEADOS
@router.get("/", summary="Listado de productos", response_model=List[ProductoOut])
async def api_listar_productos(
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    return listar_productos(db)

@router.get("/categorias", summary="Listado de categorías", response_model=List[CategoriaOut])
async def api_listar_categorias(
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    return listar_categorias(db)

@router.get(
    "/categorias/{codobjeto}/productos",
    summary="Productos por categoría",
    response_model=List[ProductoPorCategoriaOut],
)
async def api_productos_por_categoria(
    codobjeto: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    return ver_productos_por_categoria(db, codobjeto)

@router.get(
    "/buscar",
    summary="Buscar productos por nombre y/o código de categoría",
    response_model=List[ProductoOut],
)
async def api_buscar_productos(
    nomproducto: Optional[str] = Query(default=None, description="Nombre parcial o completo del producto"),
    codobjeto: Optional[int] = Query(default=None, description="Código de categoría"),
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    if nomproducto is None and codobjeto is None:
        raise HTTPException(status_code=400, detail="Debe proporcionar nomproducto y/o codobjeto")
    return buscar_productos(db, nomproducto, codobjeto)

@router.get(
    "/verCategoriasyUnidadesMedida",
    summary="Categorías y unidades de medida para previo creación de productos",
    response_model=CatalogosProductoOut,
)
async def api_listar_categorias_y_unidades(
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    return listar_categorias_y_unidades(db)



##USUARIOS EMPLEADOS ALMACEN
@router.post(
    "/crearProducto",
    summary="Crear producto",
    response_model=ProductoCreateOut,
    status_code=201,
)
async def api_crear_producto(
    payload: ProductoCreateIn,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    creadopor = (
        current_user.get("username")
        or current_user.get("user_name")
        or current_user.get("email")
        or current_user.get("sub")
        or "api"
    )
    try:
        new_id = crear_producto(db, payload, creadopor)
        return ProductoCreateOut(idproducto=new_id, message="Producto creado correctamente")
    except Exception as ex:
        raise HTTPException(status_code=400, detail=f"No se pudo crear el producto: {ex}")

@router.post(
    "/categorias",
    summary="Crear categoría",
    response_model=CategoriaCreateOut,
    status_code=201,
)
async def api_crear_categoria(
    payload: CategoriaCreateIn,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    creadopor = (
        current_user.get("username")
        or current_user.get("user_name")
        or current_user.get("email")
        or current_user.get("sub")
        or "api"
    )
    try:
        new_id = crear_categoria(db, payload, creadopor)
        return CategoriaCreateOut(idcategoria=new_id, message="Categoría creada correctamente")
    except Exception as ex:
        raise HTTPException(status_code=400, detail=f"No se pudo crear la categoría: {ex}")

@router.put(
    "/categorias/{idcategoria}",
    summary="Editar categoría",
    response_model=CategoriaUpdateOut,
)
async def api_editar_categoria(
    idcategoria: UUID,
    payload: CategoriaUpdateIn,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    actualizadopor = (
        current_user.get("username")
        or current_user.get("user_name")
        or current_user.get("email")
        or current_user.get("sub")
        or "api"
    )
    try:
        ok = editar_categoria(db, idcategoria, payload, actualizadopor)
        if not ok:
            raise HTTPException(status_code=400, detail="No se actualizó la categoría")
        return CategoriaUpdateOut(idcategoria=idcategoria, message="Categoría actualizada correctamente")
    except HTTPException:
        raise
    except Exception as ex:
        raise HTTPException(status_code=400, detail=f"No se pudo editar la categoría: {ex}")

@router.get(
    "/categorias/buscar",
    summary="Buscar categoría por código",
    response_model=List[CategoriaOut],
)
async def api_buscar_categoria(
    codobjeto: int = Query(..., description="Código de categoría"),
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    return buscar_categoria(db, codobjeto)
