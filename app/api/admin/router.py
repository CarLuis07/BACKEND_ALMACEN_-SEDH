from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
import os

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.admin.schemas import (
    DependenciaOut,
    RolOut,
    EmpleadoListOut,
    CrearEmpleadoIn,
    CrearEmpleadoOut,
    AsignarRolIn,
    AsignarRolOut,
    ActualizarEmpleadoIn,
    CambiarEstadoIn,
    CambiarContrasenaIn,
    CrearDependenciaIn,
    ActualizarDependenciaIn,
    CrearRolIn,
    ActualizarRolIn
)
from app.repositories.admin import (
    obtener_todas_dependencias,
    obtener_todos_roles,
    obtener_todos_empleados,
    buscar_empleado_por_dni,
    crear_empleado_completo,
    asignar_rol_empleado_con_password,
    actualizar_empleado,
    cambiar_estado_empleado,
    cambiar_contrasena_empleado,
    eliminar_rol_empleado,
    crear_dependencia,
    actualizar_dependencia,
    eliminar_dependencia,
    crear_rol,
    actualizar_rol,
    eliminar_rol
)

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])

# ==================== PÁGINA HTML ====================

@router.get("/", include_in_schema=False)
async def pagina_admin():
    """Sirve la página HTML de administración"""
    html_path = os.path.join(os.path.dirname(__file__), "admin.html")
    return FileResponse(html_path)

@router.get("/completo", include_in_schema=False)
async def pagina_admin_completo():
    """Sirve la página HTML de administración completa con todas las funcionalidades"""
    html_path = os.path.join(os.path.dirname(__file__), "admin_completo.html")
    return FileResponse(html_path)

# ==================== DEPENDENCIAS ====================

@router.get(
    "/dependencias",
    response_model=List[DependenciaOut],
    summary="Listar todas las dependencias"
)
async def listar_dependencias(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Obtiene la lista completa de dependencias (áreas) disponibles.
    Útil para seleccionar al crear empleados.
    """
    try:
        dependencias = obtener_todas_dependencias(db)
        return dependencias
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener dependencias: {str(e)}"
        )

# ==================== ROLES ====================

@router.get(
    "/roles",
    response_model=List[RolOut],
    summary="Listar todos los roles"
)
async def listar_roles(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Obtiene la lista completa de roles disponibles.
    Útil para asignar roles al crear empleados.
    """
    try:
        roles = obtener_todos_roles(db)
        return roles
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener roles: {str(e)}"
        )

# ==================== EMPLEADOS ====================

@router.get(
    "/empleados",
    response_model=List[EmpleadoListOut],
    summary="Listar todos los empleados"
)
async def listar_empleados(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Obtiene la lista completa de empleados con sus dependencias y roles.
    Muestra información detallada incluyendo jefe inmediato.
    """
    try:
        empleados = obtener_todos_empleados(db)
        return empleados
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener empleados: {str(e)}"
        )

@router.post(
    "/empleados",
    response_model=CrearEmpleadoOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nuevo empleado"
)
async def crear_nuevo_empleado(
    payload: CrearEmpleadoIn,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Crea un nuevo empleado en el sistema con los siguientes datos:
    - Email institucional
    - Nombre completo
    - Dependencia (área)
    - DNI (13 dígitos)
    - DNI del jefe inmediato (opcional)
    - Uno o más roles con contraseña
    
    El empleado se crea activo y se le asignan los roles especificados.
    """
    try:
        # Validar que el DNI no exista
        empleado_existente = buscar_empleado_por_dni(db, payload.dni)
        if empleado_existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Ya existe un empleado con DNI {payload.dni}"
            )
        
        # Validar que el jefe inmediato exista (si se proporciona)
        if payload.dniJefeInmediato:
            jefe = buscar_empleado_por_dni(db, payload.dniJefeInmediato)
            if not jefe:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No se encontró empleado con DNI {payload.dniJefeInmediato} para asignar como jefe"
                )
        
        # Crear el empleado
        email_usuario = current_user.get("sub", "Admin")
        empleado = crear_empleado_completo(
            db=db,
            email=payload.email,
            nombre=payload.nombre.upper(),
            id_dependencia=payload.idDependencia,
            dni=payload.dni,
            dni_jefe=payload.dniJefeInmediato,
            creado_por=email_usuario
        )
        
        # Asignar roles
        for rol_asignacion in payload.roles:
            asignar_rol_empleado_con_password(
                db=db,
                email=payload.email,
                id_rol=rol_asignacion.idRol,
                contrasena=rol_asignacion.contrasena,
                creado_por=email_usuario
            )
        
        return CrearEmpleadoOut(
            emailinstitucional=empleado["emailinstitucional"],
            nombre=empleado["nombre"],
            dni=empleado["dni"],
            mensaje=f"Empleado creado exitosamente con {len(payload.roles)} rol(es) asignado(s)"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear empleado: {str(e)}"
        )

@router.put(
    "/empleados/{email}",
    summary="Actualizar datos de un empleado"
)
async def actualizar_datos_empleado(
    email: str,
    payload: ActualizarEmpleadoIn,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Actualiza los datos de un empleado existente:
    - Nombre
    - Dependencia
    - DNI del jefe inmediato
    """
    try:
        email_usuario = current_user.get("sub", "Admin")
        resultado = actualizar_empleado(
            db=db,
            email=email,
            datos=payload.dict(exclude_unset=True),
            actualizado_por=email_usuario
        )
        return resultado
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar empleado: {str(e)}"
        )

@router.put(
    "/empleados/{email}/estado",
    summary="Dar de baja o activar empleado"
)
async def cambiar_estado_de_empleado(
    email: str,
    payload: CambiarEstadoIn,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Activa o desactiva (da de baja) a un empleado.
    Cuando se desactiva, el empleado no podrá iniciar sesión.
    """
    try:
        resultado = cambiar_estado_empleado(db, email, payload.activo)
        return resultado
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al cambiar estado: {str(e)}"
        )

@router.put(
    "/empleados/{email}/contrasena",
    summary="Cambiar contraseña de un empleado"
)
async def cambiar_password_empleado(
    email: str,
    payload: CambiarContrasenaIn,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Cambia la contraseña de un empleado (para todos sus roles).
    """
    try:
        resultado = cambiar_contrasena_empleado(
            db=db,
            email=email,
            nueva_contrasena=payload.nuevaContrasena
        )
        return resultado
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al cambiar contraseña: {str(e)}"
        )

@router.post(
    "/empleados/asignar-rol",
    response_model=AsignarRolOut,
    summary="Asignar o cambiar rol a empleado existente"
)
async def asignar_rol_a_empleado(
    payload: AsignarRolIn,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Asigna un nuevo rol a un empleado existente o actualiza su contraseña.
    Si el empleado ya tiene ese rol, actualiza la contraseña.
    """
    try:
        email_usuario = current_user.get("sub", "Admin")
        
        # Asignar o actualizar el rol
        asignar_rol_empleado_con_password(
            db=db,
            email=payload.email,
            id_rol=payload.idRol,
            contrasena=payload.contrasena,
            creado_por=email_usuario
        )
        
        return AsignarRolOut(
            mensaje=f"Rol asignado exitosamente a {payload.email}"
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al asignar rol: {str(e)}"
        )

@router.delete(
    "/empleados/{email}/roles/{id_rol}",
    summary="Eliminar rol de un empleado"
)
async def quitar_rol_empleado(
    email: str,
    id_rol: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Elimina un rol específico de un empleado.
    """
    try:
        resultado = eliminar_rol_empleado(db, email, id_rol)
        return resultado
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar rol: {str(e)}"
        )

# ==================== DEPENDENCIAS CRUD ====================

@router.post(
    "/dependencias",
    status_code=status.HTTP_201_CREATED,
    summary="Crear nueva dependencia"
)
async def crear_nueva_dependencia(
    payload: CrearDependenciaIn,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Crea una nueva dependencia (área organizacional).
    """
    try:
        email_usuario = current_user.get("sub", "Admin")
        resultado = crear_dependencia(
            db=db,
            datos=payload.dict(),
            creado_por=email_usuario
        )
        return resultado
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear dependencia: {str(e)}"
        )

@router.put(
    "/dependencias/{id_dependencia}",
    summary="Actualizar dependencia"
)
async def actualizar_datos_dependencia(
    id_dependencia: str,
    payload: ActualizarDependenciaIn,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Actualiza los datos de una dependencia existente.
    """
    try:
        email_usuario = current_user.get("sub", "Admin")
        resultado = actualizar_dependencia(
            db=db,
            id_dependencia=id_dependencia,
            datos=payload.dict(exclude_unset=True),
            actualizado_por=email_usuario
        )
        return resultado
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar dependencia: {str(e)}"
        )

@router.delete(
    "/dependencias/{id_dependencia}",
    summary="Eliminar dependencia"
)
async def eliminar_una_dependencia(
    id_dependencia: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Elimina una dependencia.
    No se puede eliminar si tiene empleados asociados.
    """
    try:
        resultado = eliminar_dependencia(db, id_dependencia)
        return resultado
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar dependencia: {str(e)}"
        )

# ==================== ROLES CRUD ====================

@router.post(
    "/roles",
    status_code=status.HTTP_201_CREATED,
    summary="Crear nuevo rol"
)
async def crear_nuevo_rol(
    payload: CrearRolIn,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Crea un nuevo rol en el sistema.
    """
    try:
        resultado = crear_rol(db, payload.dict())
        return resultado
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear rol: {str(e)}"
        )

@router.put(
    "/roles/{id_rol}",
    summary="Actualizar rol"
)
async def actualizar_datos_rol(
    id_rol: int,
    payload: ActualizarRolIn,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Actualiza los datos de un rol existente.
    """
    try:
        resultado = actualizar_rol(
            db=db,
            id_rol=id_rol,
            datos=payload.dict(exclude_unset=True)
        )
        return resultado
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar rol: {str(e)}"
        )

@router.delete(
    "/roles/{id_rol}",
    summary="Eliminar rol"
)
async def eliminar_un_rol(
    id_rol: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Elimina un rol del sistema.
    No se puede eliminar si hay empleados con ese rol.
    """
    try:
        resultado = eliminar_rol(db, id_rol)
        return resultado
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar rol: {str(e)}"
        )
