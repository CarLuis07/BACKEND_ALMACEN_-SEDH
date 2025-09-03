from pydantic import BaseModel, EmailStr
from datetime import date

class EmpleadoBase(BaseModel):
    EmailInstitucional: EmailStr
    Nombre: str | None = None
    IdDependencia: str | None = None
    DNI: str | None = None
    DNIJefeInmediato: str | None = None

class EmpleadoCreate(EmpleadoBase):
    pass

class EmpleadoRead(EmpleadoBase):
    CreadoEn: date | None = None
    CreadoPor: str | None = None
    ActualizadoEn: date | None = None
    ActualizadoPor: str | None = None

    class Config:
        from_attributes = True