from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel, model_validator
from datetime import date

class ProductoItemIn(BaseModel):
    idProducto: UUID
    nombre: Optional[str] = None
    cantidad: Decimal
    gasUnitario: Decimal
    gasTotalProducto: Optional[Decimal] = None

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
    codrequisicion: str
    nombrejefeInmediato: str
    emailjefeInmediato: str

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

class ProductoModificadoIn(BaseModel):
    idProducto: UUID
    cantidad: Decimal

class ResponderRequisicionIn(BaseModel):
    idRequisicion: UUID
    estado: str 
    comentario: Optional[str] = None
    productos: Optional[List[ProductoModificadoIn]] = None  # Productos modificados (opcional)

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
    nuevaCantidad: Optional[Decimal] = None
    cantidad: Optional[Decimal] = None

    @model_validator(mode="after")
    def _normaliza_cantidad(self):
        # Aceptar alias "cantidad" para compatibilidad con frontend anterior
        if self.nuevaCantidad is None and self.cantidad is not None:
            self.nuevaCantidad = self.cantidad
        if self.nuevaCantidad is None:
            raise ValueError("nuevaCantidad es obligatoria")
        return self

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


# --- JEFE DE MATERIALES ---
class RequisicionPendienteJefeMaterialesOut(BaseModel):
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

class ProductoAjusteJefeMaterialesIn(BaseModel):
    idProducto: UUID
    nuevaCantidad: Optional[Decimal] = None
    cantidad: Optional[Decimal] = None

    @model_validator(mode="after")
    def _normaliza_cantidad(self):
        if self.nuevaCantidad is None and self.cantidad is not None:
            self.nuevaCantidad = self.cantidad
        if self.nuevaCantidad is None:
            raise ValueError("nuevaCantidad es obligatoria")
        return self

class ResponderRequisicionJefeMaterialesIn(BaseModel):
    idRequisicion: UUID
    estado: str  # "APROBADO" | "RECHAZADO"
    comentario: Optional[str] = None
    productos: List[ProductoAjusteJefeMaterialesIn] = []

    @model_validator(mode="after")
    def _normaliza_y_valida(self):
        est = (self.estado or "").strip().upper()
        if est not in {"APROBADO", "RECHAZADO"}:
            raise ValueError("Estado inválido: solo APROBADO o RECHAZADO")
        if est == "RECHAZADO" and (self.comentario is None or self.comentario.strip() == ""):
            raise ValueError("Comentario es obligatorio si se rechaza la requisición")
        self.estado = est
        return self


# --- ALMACÉN ---
class RequisicionPendienteAlmacenOut(BaseModel):
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

class ProductoEntregaAlmacenIn(BaseModel):
    idProducto: UUID
    cantidadEntregada: int

class ResponderRequisicionAlmacenIn(BaseModel):
    idRequisicion: UUID
    emailRecibido: str  # Nombre de quien recibe
    productos: List[ProductoEntregaAlmacenIn]
