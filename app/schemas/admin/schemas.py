from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from uuid import UUID
from datetime import date

# ==================== DEPENDENCIAS ====================

class DependenciaOut(BaseModel):
    iddependencia: UUID
    nomdependencia: str
    idprograma: int
    sigla: str
    creadoen: date

# ==================== ROLES ====================

class RolOut(BaseModel):
    idrol: UUID
    nomrol: str
    desrol: Optional[str] = None

# ==================== EMPLEADOS ====================

class EmpleadoListOut(BaseModel):
    emailinstitucional: str
    nombre: str
    dni: str
    dnijefeinmediato: Optional[str] = None
    nomdependencia: str
    sigladependencia: str
    iddependencia: UUID
    nombrejefeinmediato: Optional[str] = None
    roles: Optional[str] = None
    activo: bool
    creadoen: date

class RolAsignacion(BaseModel):
    idRol: UUID
    contrasena: str = Field(min_length=6, description="Contraseña mínimo 6 caracteres")

class CrearEmpleadoIn(BaseModel):
    email: EmailStr
    nombre: str = Field(min_length=3, max_length=200)
    idDependencia: UUID
    dni: str = Field(pattern=r'^\d{13}$', description="DNI debe tener 13 dígitos")
    dniJefeInmediato: Optional[str] = Field(None, pattern=r'^\d{13}$', description="DNI del jefe debe tener 13 dígitos")
    roles: List[RolAsignacion] = Field(min_length=1, description="Debe asignar al menos un rol")

class CrearEmpleadoOut(BaseModel):
    emailinstitucional: str
    nombre: str
    dni: str
    mensaje: str

class AsignarRolIn(BaseModel):
    email: EmailStr
    idRol: UUID
    contrasena: str = Field(min_length=6, description="Contraseña mínimo 6 caracteres")

class AsignarRolOut(BaseModel):
    mensaje: str

class ActualizarEmpleadoIn(BaseModel):
    nombre: Optional[str] = Field(None, min_length=3, max_length=200)
    idDependencia: Optional[UUID] = None
    dniJefeInmediato: Optional[str] = Field(None, pattern=r'^\d{13}$', description="DNI del jefe debe tener 13 dígitos")

class CambiarEstadoIn(BaseModel):
    activo: bool = Field(description="True para activar, False para dar de baja")

class CambiarContrasenaIn(BaseModel):
    nuevaContrasena: str = Field(min_length=6, description="Nueva contraseña mínimo 6 caracteres")

# ==================== DEPENDENCIAS CRUD ====================

class CrearDependenciaIn(BaseModel):
    nomdependencia: str = Field(min_length=3, max_length=255)
    sigla: str = Field(min_length=2, max_length=20)
    idPrograma: Optional[int] = Field(1, description="ID del programa al que pertenece")

class ActualizarDependenciaIn(BaseModel):
    nomdependencia: Optional[str] = Field(None, min_length=3, max_length=255)
    sigla: Optional[str] = Field(None, min_length=2, max_length=20)

# ==================== ROLES CRUD ====================

class CrearRolIn(BaseModel):
    nomrol: str = Field(min_length=3, max_length=100)
    descripcion: Optional[str] = Field(None, max_length=500)

class ActualizarRolIn(BaseModel):
    nomrol: Optional[str] = Field(None, min_length=3, max_length=100)
    descripcion: Optional[str] = Field(None, max_length=500)
