"""
Decoradores y utilidades para control de acceso y permisos
"""
from functools import wraps
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.repositories.admin import verificar_es_administrador
from typing import Dict, Any

def requiere_administrador(func):
    """Decorador que requiere que el usuario sea Administrador"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Extraer current_user y db de los argumentos
        current_user = None
        db = None
        
        for key, value in kwargs.items():
            if key == 'current_user':
                current_user = value
            elif key == 'db':
                db = value
        
        if not current_user or not db:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error interno: faltan dependencias"
            )
        
        # Obtener email del usuario
        email = (str(current_user.get("email") or current_user.get("sub") or "")).strip()
        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido"
            )
        
        # Verificar si es administrador
        if not verificar_es_administrador(db, email):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acceso denegado: se requieren permisos de Administrador"
            )
        
        return await func(*args, **kwargs)
    return wrapper

def verificar_permisos_modulo(modulo: str, accion: str):
    """
    Decorador para verificar permisos específicos de módulo
    modulo: 'productos', 'requisiciones', 'accesos', etc.
    accion: 'crear', 'leer', 'actualizar', 'eliminar'
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extraer current_user de los argumentos
            current_user = None
            for key, value in kwargs.items():
                if key == 'current_user':
                    current_user = value
                    break
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error interno: falta información del usuario"
                )
            
            # Obtener el rol del usuario
            rol = current_user.get("role", "").strip()
            
            # Los administradores tienen acceso a todo
            if rol == "Administrador":
                return await func(*args, **kwargs)
            
            # Verificar permisos específicos por rol y módulo
            permisos_rol = obtener_permisos_rol(rol)
            
            if not tiene_permiso(permisos_rol, modulo, accion):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Acceso denegado: no tienes permisos para {accion} en {modulo}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def obtener_permisos_rol(rol: str) -> Dict[str, list]:
    """
    Define los permisos por rol
    Retorna un diccionario con los módulos y acciones permitidas
    """
    permisos = {
        "Administrador": {
            "productos": ["crear", "leer", "actualizar", "eliminar"],
            "categorias": ["crear", "leer", "actualizar", "eliminar"],
            "requisiciones": ["crear", "leer", "actualizar", "eliminar", "aprobar"],
            "accesos": ["crear", "leer", "actualizar", "eliminar"],
            "movimientos": ["crear", "leer", "actualizar", "eliminar"],
            "dashboard": ["leer"]
        },
        "EmpAlmacen": {
            "productos": ["crear", "leer", "actualizar"],
            "categorias": ["leer"],
            "requisiciones": ["leer", "entregar"],
            "movimientos": ["crear", "leer"],
            "dashboard": ["leer"]
        },
        "JefSerMat": {
            "productos": ["leer"],
            "categorias": ["leer"],
            "requisiciones": ["leer", "aprobar"],
            "movimientos": ["leer"],
            "dashboard": ["leer"]
        },
        "GerAdmon": {
            "productos": ["leer"],
            "categorias": ["leer"],
            "requisiciones": ["leer", "aprobar"],
            "movimientos": ["leer"],
            "dashboard": ["leer"]
        },
        "JefInmediato": {
            "productos": ["leer"],
            "categorias": ["leer"],
            "requisiciones": ["crear", "leer", "aprobar"],
            "dashboard": ["leer"]
        },
        "Empleado": {
            "productos": ["leer"],
            "categorias": ["leer"],
            "requisiciones": ["crear", "leer"],
            "dashboard": ["leer"]
        },
        "Auditor": {
            "productos": ["leer"],
            "categorias": ["leer"],
            "requisiciones": ["leer"],
            "movimientos": ["leer"],
            "dashboard": ["leer"]
        }
    }
    
    return permisos.get(rol, {})

def tiene_permiso(permisos_rol: Dict[str, list], modulo: str, accion: str) -> bool:
    """
    Verifica si un rol tiene permiso para una acción específica en un módulo
    """
    if modulo not in permisos_rol:
        return False
    
    return accion in permisos_rol[modulo]

def obtener_modulos_usuario(rol: str) -> list:
    """
    Obtiene la lista de módulos a los que tiene acceso un rol
    """
    permisos = obtener_permisos_rol(rol)
    return list(permisos.keys())

def es_administrador_usuario(current_user: Dict[str, Any]) -> bool:
    """
    Verifica si el usuario actual es administrador basado en el token
    """
    rol = current_user.get("role", "").strip()
    return rol == "Administrador"