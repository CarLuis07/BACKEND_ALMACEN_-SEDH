from typing import Optional, List
from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel, ConfigDict
from datetime import date


##usuarios EMPLEADOS
class CategoriaOut(BaseModel):
    codobjeto: Optional[int] = None
    nomcategoria: Optional[str] = None
    descategoria: Optional[str] = None
    imagen: Optional[bytes] = None

class ProductoPorCategoriaOut(BaseModel):
    idproducto: UUID
    codobjeto: int
    nomproducto: Optional[str] = None
    descproducto: Optional[str] = None
    canstock: Optional[Decimal] = None
    gasunitario: Optional[Decimal] = None

class ProductoOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    idproducto: UUID
    nomproducto: Optional[str] = None
    nomcategoria: Optional[str] = None
    descproducto: Optional[str] = None
    canstock: Optional[Decimal] = None
    gasunitario: Optional[Decimal] = None
    CodObjetoUnico: Optional[str] = None  # Usar el nombre del modelo ORM (PascalCase)
    codobjetunico: Optional[str] = None   # Alias para compatibilidad con frontend
    facturas: Optional[str] = None
    ordenescompra: Optional[str] = None
    fecvencimiento: Optional[date] = None

# ver lista categorias previo agregar producto
class CategoriaRefOut(BaseModel):
    idcategoria: UUID
    codobjeto: Optional[int] = None
    nomcategoria: Optional[str] = None

# ver lista unidades de medida previo agregar producto
class UnidadMedidaOut(BaseModel):
    idunidadmedida: UUID
    nomunidad: Optional[str] = None

#salida conjunta de categorias y unidades de medida previo agregar producto
class CatalogosProductoOut(BaseModel):
    categorias: List[CategoriaRefOut]
    unidades: List[UnidadMedidaOut]



##usuarios EMPLEADO ALMACEN
# Crear producto
class ProductoCreateIn(BaseModel):
    idcategoria: UUID
    fecingreso: date
    nomproducto: str
    descproducto: Optional[str] = None
    canstock: Decimal          # Stock inicial (función BD lo duplica como CantStockInicial)
    proveedor: Optional[str] = None
    limstockbajo: Decimal
    fecvencimiento: Optional[date] = None
    idunidadmedida: UUID
    gasunitario: Decimal
    gastotal: Decimal          # Gasto inicial (función BD lo duplica como GasTotalInicial)
    # Campos opcionales
    facturas: Optional[str] = None
    ordenescompra: Optional[str] = None

class ProductoCreateOut(BaseModel):
    idproducto: Optional[UUID] = None
    message: str


# Crear una nueva categoría
class CategoriaCreateIn(BaseModel):
    codobjeto: int
    nomcategoria: str
    descategoria: Optional[str] = None
    imagen: Optional[bytes] = None  # enviar como base64 en JSON

class CategoriaCreateOut(BaseModel):
    idcategoria: Optional[UUID] = None
    message: str

# Editar categoría
class CategoriaUpdateIn(BaseModel):
    codobjeto: Optional[int] = None
    nomcategoria: Optional[str] = None
    descategoria: Optional[str] = None
    imagen: Optional[bytes] = None  # enviar como base64 en JSON

class CategoriaUpdateOut(BaseModel):
    idcategoria: UUID
    message: str