from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel, model_validator
from datetime import date

class ProductoItemIn(BaseModel):
    nombre: str
    cantidad: Decimal
    gasUnitario: Decimal
    gasTotalProducto: Decimal

#EMPLEADOS
class CrearRequisicionIn(BaseModel):
    email: Optional[str] = None
    proIntermedio: Decimal
    proFinal: int
    obsEmpleado: Optional[str] = None
    gasTotalPedido: Decimal
    productos: List[ProductoItemIn]

class CrearRequisicionOut(BaseModel):
    idrequisicion: UUID

# JEFES INMEDIATOS
class ProductoItemOut(BaseModel):
    idProducto: UUID
    nombre: str
    cantidad: Decimal
    gasUnitario: Decimal
    gasTotalProducto: Decimal

class RequisicionPendienteOut(BaseModel):
    idRequisicion: UUID
    codRequisicion: str
    nombreSubordinado: str
    dependencia: str
    fecSolicitud: date
    codPrograma: int
    proIntermedio: Decimal
    proFinal: int
    obsEmpleado: Optional[str] = None
    gasTotalDelPedido: Decimal
    productos: List[ProductoItemOut]

class ResponderRequisicionIn(BaseModel):
    idRequisicion: UUID
    estado: str 
    comentario: Optional[str] = None

    @model_validator(mode="after")
    def _normaliza_y_valida(self):
        est = (self.estado or "").strip().upper()
        if est not in {"APROBADO", "RECHAZADO"}:
            raise ValueError("Estado inválido: solo APROBADO o RECHAZADO")
        if est == "RECHAZADO" and (self.comentario is None or self.comentario.strip() == ""):
            raise ValueError("Comentario es obligatorio si se rechaza la requisición")
        self.estado = est
        return self

class ResponderRequisicionOut(BaseModel):
    mensaje: str

# --- GERENTE ADMINISTRATIVO ---
class RequisicionPendienteGerenteOut(BaseModel):
    idRequisicion: UUID
    codRequisicion: str
    nombreEmpleado: str
    dependencia: str
    fecSolicitud: date
    codPrograma: int
    proIntermedio: Decimal
    proFinal: int
    obsEmpleado: Optional[str] = None
    gasTotalDelPedido: Decimal
    productos: List[ProductoItemOut]

# para responder ---
class ProductoAjusteGerenteIn(BaseModel):
    idProducto: UUID
    nuevaCantidad: Decimal

class ResponderRequisicionGerenteIn(BaseModel):
    idRequisicion: UUID
    estado: str  # "APROBADO" | "RECHAZADO"
    comentario: Optional[str] = None
    productos: List[ProductoAjusteGerenteIn] = []

    @model_validator(mode="after")
    def _normaliza_y_valida(self):
        est = (self.estado or "").strip().upper()
        if est not in {"APROBADO", "RECHAZADO"}:
            raise ValueError("Estado inválido: solo APROBADO o RECHAZADO")
        if est == "RECHAZADO" and (self.comentario is None or self.comentario.strip() == ""):
            raise ValueError("Comentario es obligatorio si se rechaza la requisición")
        self.estado = est
        return self

