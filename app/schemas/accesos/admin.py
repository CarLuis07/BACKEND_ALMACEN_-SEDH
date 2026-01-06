"""
Schemas para funcionalidades de administración de accesos
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID

# --- Esquemas para gestión de empleados ---
class EmpleadoOut(BaseModel):
    """Información completa de un empleado"""
    emailinstitucional: str
    nombres: Optional[str] = None
    apellidos: Optional[str] = None
    dni: Optional[str] = None
    actlaboralmente: Optional[bool] = None
    idrol: Optional[UUID] = None
    nomrol: Optional[str] = None
    iddependencia: Optional[UUID] = None
    nomdependencia: Optional[str] = None
    ultimologin: Optional[datetime] = None

class EmpleadoCreateIn(BaseModel):
    """Datos para crear un nuevo empleado"""
    emailinstitucional: str = Field(..., description="Email institucional del empleado")
    nombres: str = Field(..., description="Nombres del empleado")
    apellidos: str = Field(..., description="Apellidos del empleado")
    dni: Optional[str] = Field(None, description="DNI del empleado")
    contrasena: str = Field(..., description="Contraseña del empleado")
    idrol: UUID = Field(..., description="ID del rol a asignar")
    iddependencia: Optional[UUID] = Field(None, description="ID de la dependencia")
    actlaboralmente: bool = Field(True, description="Estado laboral activo")

class EmpleadoUpdateIn(BaseModel):
    """Datos para actualizar un empleado existente"""
    nombres: Optional[str] = None
    apellidos: Optional[str] = None
    dni: Optional[str] = None
    contrasena: Optional[str] = None
    idrol: Optional[UUID] = None
    iddependencia: Optional[UUID] = None
    actlaboralmente: Optional[bool] = None

# --- Esquemas para gestión de roles ---
class RolOut(BaseModel):
    """Información de un rol"""
    idrol: UUID
    nomrol: str

class RolCreateIn(BaseModel):
    """Datos para crear un nuevo rol"""
    nomrol: str = Field(..., description="Nombre del rol")

class RolUpdateIn(BaseModel):
    """Datos para actualizar un rol"""
    nomrol: str = Field(..., description="Nuevo nombre del rol")

# --- Esquemas para gestión de dependencias ---
class DependenciaOut(BaseModel):
    """Información de una dependencia"""
    iddependencia: UUID
    nomdependencia: str
    siglas: Optional[str] = None

class DependenciaCreateIn(BaseModel):
    """Datos para crear una nueva dependencia"""
    nomdependencia: str = Field(..., description="Nombre de la dependencia")
    siglas: Optional[str] = Field(None, description="Siglas de la dependencia")

class DependenciaUpdateIn(BaseModel):
    """Datos para actualizar una dependencia"""
    nomdependencia: Optional[str] = None
    siglas: Optional[str] = None

# --- Esquemas para permisos y módulos ---
class ModuloOut(BaseModel):
    """Información de un módulo del sistema"""
    nombre: str
    descripcion: str
    activo: bool

class PermisoOut(BaseModel):
    """Información de permisos de un rol"""
    idrol: UUID
    nomrol: str
    modulos: List[str]
    permisos: List[str]  # crear, leer, actualizar, eliminar

class AsignarRolIn(BaseModel):
    """Datos para asignar un rol a un empleado"""
    emailinstitucional: str = Field(..., description="Email del empleado")
    idrol: UUID = Field(..., description="ID del nuevo rol")

# --- Respuestas de operaciones ---
class OperacionExitosaOut(BaseModel):
    """Respuesta estándar para operaciones exitosas"""
    mensaje: str
    exito: bool = True
    datos: Optional[dict] = None

class EstadisticasAdminOut(BaseModel):
    """Estadísticas del sistema para el administrador"""
    total_empleados: int
    empleados_activos: int
    total_roles: int
    total_dependencias: int
    total_requisiciones: int
    requisiciones_pendientes: int
    requisiciones_aprobadas: int
    total_productos: int
    productos_activos: int