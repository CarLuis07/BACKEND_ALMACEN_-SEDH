"""
Router para funcionalidades administrativas
Solo accesible para usuarios con rol 'Administrador'
"""
import sys
import os
import logging
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

logger = logging.getLogger(__name__)

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.permissions import requiere_administrador, es_administrador_usuario
from app.core.modulos_permisos import (
    obtener_modulos_por_rol, verificar_acceso_modulo, obtener_informacion_rol,
    obtener_todos_los_roles, obtener_modulos_disponibles, generar_matriz_permisos
)
from app.repositories.admin import (
    verificar_es_administrador, listar_empleados, obtener_empleado, 
    crear_empleado, actualizar_empleado, cambiar_estado_empleado,
    listar_roles, crear_rol, actualizar_rol, asignar_rol_empleado,
    listar_dependencias, crear_dependencia, obtener_estadisticas_admin,
    obtener_modulos_personalizados, asignar_modulos_personalizados,
    obtener_empleados_con_permisos_completos, eliminar_permisos_personalizados
)
from app.schemas.accesos.admin import (
    EmpleadoOut, EmpleadoCreateIn, EmpleadoUpdateIn,
    RolOut, RolCreateIn, RolUpdateIn,
    DependenciaOut, DependenciaCreateIn, DependenciaUpdateIn,
    AsignarRolIn, OperacionExitosaOut, EstadisticasAdminOut
)

router = APIRouter()

# --- VERIFICACIÓN DE PERMISOS ---
@router.get("/verificar-admin", summary="Verificar si el usuario es administrador")
async def verificar_admin(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verifica si el usuario actual tiene permisos de administrador"""
    email = (str(current_user.get("email") or current_user.get("sub") or "")).strip()
    if not email:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    es_admin = verificar_es_administrador(db, email)
    
    return {
        "es_administrador": es_admin,
        "email": email,
        "rol": current_user.get("rol", current_user.get("role", "")),
        "modulos_disponibles": [
            "Gestión de Empleados",
            "Gestión de Roles", 
            "Gestión de Dependencias",
            "Agregar Productos",
            "Ver Categorías",
            "Ver Productos",
            "Movimientos",
            "Gestión de Accesos",
            "Estadísticas del Sistema"
        ] if es_admin else []
    }

# --- ESTADÍSTICAS DEL SISTEMA ---
@router.get("/estadisticas", summary="Estadísticas del sistema", response_model=EstadisticasAdminOut)
async def obtener_estadisticas(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene estadísticas generales del sistema para el administrador"""
    email = (str(current_user.get("email") or current_user.get("sub") or "")).strip()
    if not email:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    if not verificar_es_administrador(db, email):
        raise HTTPException(status_code=403, detail="Acceso denegado: se requieren permisos de Administrador")
    
    try:
        estadisticas = obtener_estadisticas_admin(db)
        return EstadisticasAdminOut(**estadisticas)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo estadísticas: {str(e)}")

# --- GESTIÓN DE EMPLEADOS ---
@router.get("/empleados", summary="Listar todos los empleados", response_model=List[EmpleadoOut])
async def listar_todos_empleados(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lista todos los empleados del sistema"""
    email = (str(current_user.get("email") or current_user.get("sub") or "")).strip()
    if not email:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    if not verificar_es_administrador(db, email):
        raise HTTPException(status_code=403, detail="Acceso denegado: se requieren permisos de Administrador")
    
    try:
        empleados = listar_empleados(db)
        return [EmpleadoOut(**empleado) for empleado in empleados]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listando empleados: {str(e)}")

@router.get("/empleados/{email_empleado}", summary="Obtener empleado específico", response_model=EmpleadoOut)
async def obtener_empleado_especifico(
    email_empleado: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene información de un empleado específico"""
    email = (str(current_user.get("email") or current_user.get("sub") or "")).strip()
    if not email:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    if not verificar_es_administrador(db, email):
        raise HTTPException(status_code=403, detail="Acceso denegado: se requieren permisos de Administrador")
    
    try:
        empleado = obtener_empleado(db, email_empleado)
        if not empleado:
            raise HTTPException(status_code=404, detail="Empleado no encontrado")
        return EmpleadoOut(**empleado)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo empleado: {str(e)}")

@router.post("/empleados", summary="Crear nuevo empleado", response_model=OperacionExitosaOut)
async def crear_nuevo_empleado(
    empleado_data: EmpleadoCreateIn,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crea un nuevo empleado en el sistema"""
    email = (str(current_user.get("email") or current_user.get("sub") or "")).strip()
    if not email:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    if not verificar_es_administrador(db, email):
        raise HTTPException(status_code=403, detail="Acceso denegado: se requieren permisos de Administrador")
    
    try:
        datos = empleado_data.model_dump()
        # Convertir UUID a string para la base de datos
        datos["idrol"] = str(datos["idrol"])
        if datos.get("iddependencia"):
            datos["iddependencia"] = str(datos["iddependencia"])
            
        resultado = crear_empleado(db, datos)
        return OperacionExitosaOut(mensaje=resultado["mensaje"], datos=resultado)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creando empleado: {str(e)}")

@router.put("/empleados/{email_empleado}", summary="Actualizar empleado", response_model=OperacionExitosaOut)
async def actualizar_empleado_existente(
    email_empleado: str,
    empleado_data: EmpleadoUpdateIn,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Actualiza información de un empleado existente"""
    email = (str(current_user.get("email") or current_user.get("sub") or "")).strip()
    if not email:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    if not verificar_es_administrador(db, email):
        raise HTTPException(status_code=403, detail="Acceso denegado: se requieren permisos de Administrador")
    
    try:
        datos = empleado_data.model_dump(exclude_unset=True)
        # Convertir UUIDs a string
        if "idrol" in datos and datos["idrol"]:
            datos["idrol"] = str(datos["idrol"])
        if "iddependencia" in datos and datos["iddependencia"]:
            datos["iddependencia"] = str(datos["iddependencia"])
            
        resultado = actualizar_empleado(db, email_empleado, datos)
        return OperacionExitosaOut(mensaje=resultado["mensaje"], datos=resultado)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error actualizando empleado: {str(e)}")

@router.patch("/empleados/{email_empleado}/estado", summary="Cambiar estado de empleado", response_model=OperacionExitosaOut)
async def cambiar_estado_empleado_endpoint(
    email_empleado: str,
    activo: bool,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Activa o desactiva un empleado"""
    email = (str(current_user.get("email") or current_user.get("sub") or "")).strip()
    if not email:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    if not verificar_es_administrador(db, email):
        raise HTTPException(status_code=403, detail="Acceso denegado: se requieren permisos de Administrador")
    
    try:
        resultado = cambiar_estado_empleado(db, email_empleado, activo)
        return OperacionExitosaOut(mensaje=resultado["mensaje"], datos=resultado)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cambiando estado: {str(e)}")

# --- GESTIÓN DE ROLES ---
@router.get("/roles", summary="Listar todos los roles", response_model=List[RolOut])
async def listar_todos_roles(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lista todos los roles disponibles"""
    email = (str(current_user.get("email") or current_user.get("sub") or "")).strip()
    if not email:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    if not verificar_es_administrador(db, email):
        raise HTTPException(status_code=403, detail="Acceso denegado: se requieren permisos de Administrador")
    
    try:
        roles = listar_roles(db)
        return [RolOut(**rol) for rol in roles]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listando roles: {str(e)}")

@router.post("/roles", summary="Crear nuevo rol", response_model=OperacionExitosaOut)
async def crear_nuevo_rol(
    rol_data: RolCreateIn,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crea un nuevo rol en el sistema"""
    email = (str(current_user.get("email") or current_user.get("sub") or "")).strip()
    if not email:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    if not verificar_es_administrador(db, email):
        raise HTTPException(status_code=403, detail="Acceso denegado: se requieren permisos de Administrador")
    
    try:
        resultado = crear_rol(db, rol_data.nomrol)
        return OperacionExitosaOut(mensaje=resultado["mensaje"], datos=resultado)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creando rol: {str(e)}")

@router.put("/roles/{idrol}", summary="Actualizar rol", response_model=OperacionExitosaOut)
async def actualizar_rol_existente(
    idrol: UUID,
    rol_data: RolUpdateIn,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Actualiza el nombre de un rol"""
    email = (str(current_user.get("email") or current_user.get("sub") or "")).strip()
    if not email:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    if not verificar_es_administrador(db, email):
        raise HTTPException(status_code=403, detail="Acceso denegado: se requieren permisos de Administrador")
    
    try:
        resultado = actualizar_rol(db, idrol, rol_data.nomrol)
        return OperacionExitosaOut(mensaje=resultado["mensaje"], datos=resultado)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error actualizando rol: {str(e)}")

@router.post("/empleados/asignar-rol", summary="Asignar rol a empleado", response_model=OperacionExitosaOut)
async def asignar_rol_a_empleado(
    asignacion: AsignarRolIn,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Asigna un rol específico a un empleado"""
    email = (str(current_user.get("email") or current_user.get("sub") or "")).strip()
    if not email:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    if not verificar_es_administrador(db, email):
        raise HTTPException(status_code=403, detail="Acceso denegado: se requieren permisos de Administrador")
    
    try:
        resultado = asignar_rol_empleado(db, asignacion.emailinstitucional, asignacion.idrol)
        return OperacionExitosaOut(mensaje=resultado["mensaje"], datos=resultado)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error asignando rol: {str(e)}")

# --- GESTIÓN DE DEPENDENCIAS ---
@router.get("/dependencias", summary="Listar todas las dependencias", response_model=List[DependenciaOut])
async def listar_todas_dependencias(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lista todas las dependencias"""
    email = (str(current_user.get("email") or current_user.get("sub") or "")).strip()
    if not email:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    if not verificar_es_administrador(db, email):
        raise HTTPException(status_code=403, detail="Acceso denegado: se requieren permisos de Administrador")
    
    try:
        dependencias = listar_dependencias(db)
        return [DependenciaOut(**dep) for dep in dependencias]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listando dependencias: {str(e)}")

@router.post("/dependencias", summary="Crear nueva dependencia", response_model=OperacionExitosaOut)
async def crear_nueva_dependencia(
    dependencia_data: DependenciaCreateIn,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crea una nueva dependencia"""
    email = (str(current_user.get("email") or current_user.get("sub") or "")).strip()
    if not email:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    if not verificar_es_administrador(db, email):
        raise HTTPException(status_code=403, detail="Acceso denegado: se requieren permisos de Administrador")
    
    try:
        datos = dependencia_data.model_dump()
        resultado = crear_dependencia(db, datos)
        return OperacionExitosaOut(mensaje=resultado["mensaje"], datos=resultado)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creando dependencia: {str(e)}")

# --- GESTIÓN DE MÓDULOS Y PERMISOS ---
@router.get("/modulos", summary="Listar todos los módulos del sistema")
async def listar_modulos_sistema(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lista todos los módulos disponibles en el sistema"""
    email = (str(current_user.get("email") or current_user.get("sub") or "")).strip()
    if not email:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    if not verificar_es_administrador(db, email):
        raise HTTPException(status_code=403, detail="Acceso denegado: se requieren permisos de Administrador")
    
    modulos = obtener_modulos_disponibles()
    return {"modulos": modulos}

@router.get("/permisos-rol/{rol}", summary="Obtener permisos de un rol específico")
async def obtener_permisos_rol(
    rol: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene información detallada de permisos de un rol"""
    email = (str(current_user.get("email") or current_user.get("sub") or "")).strip()
    if not email:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    if not verificar_es_administrador(db, email):
        raise HTTPException(status_code=403, detail="Acceso denegado: se requieren permisos de Administrador")
    
    info_rol = obtener_informacion_rol(rol)
    modulos_disponibles = obtener_modulos_por_rol(rol)
    
    return {
        "rol": rol,
        "informacion": info_rol,
        "modulos_disponibles": modulos_disponibles
    }

@router.get("/matriz-permisos", summary="Obtener matriz completa de permisos")
async def obtener_matriz_permisos(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene la matriz completa de permisos rol x módulo"""
    email = (str(current_user.get("email") or current_user.get("sub") or "")).strip()
    if not email:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    if not verificar_es_administrador(db, email):
        raise HTTPException(status_code=403, detail="Acceso denegado: se requieren permisos de Administrador")
    
    matriz = generar_matriz_permisos()
    roles_info = obtener_todos_los_roles()
    
    return {
        "matriz_permisos": matriz,
        "resumen_roles": roles_info,
        "total_roles": len(roles_info),
        "total_modulos": len(obtener_modulos_disponibles())
    }

@router.get("/empleados-completo", summary="Listar empleados con información completa")
async def listar_empleados_completo(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lista todos los empleados con información completa incluyendo permisos de módulos"""
    email = (str(current_user.get("email") or current_user.get("sub") or "")).strip()
    if not email:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    if not verificar_es_administrador(db, email):
        raise HTTPException(status_code=403, detail="Acceso denegado: se requieren permisos de Administrador")
    
    try:
        empleados = listar_empleados(db)
        
        # Enriquecer con información de módulos disponibles por rol
        for empleado in empleados:
            rol = empleado.get('nomrol', 'Empleado')
            empleado['modulos_disponibles'] = obtener_modulos_por_rol(rol)
            empleado['info_rol'] = obtener_informacion_rol(rol)
            empleado['total_modulos'] = len(empleado['modulos_disponibles'])
        
        return empleados
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listando empleados: {str(e)}")

@router.get("/empleados-permisos", summary="Empleados con información completa de permisos")
async def listar_empleados_permisos_completos(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lista empleados con información completa incluyendo permisos personalizados"""
    email = (str(current_user.get("email") or current_user.get("sub") or "")).strip()
    if not email:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    if not verificar_es_administrador(db, email):
        raise HTTPException(status_code=403, detail="Acceso denegado: se requieren permisos de Administrador")
    
    try:
        empleados = obtener_empleados_con_permisos_completos(db)
        
        # Enriquecer con información de módulos por rol
        for empleado in empleados:
            rol = empleado.get('nomrol', 'Empleado')
            empleado['modulos_por_rol'] = obtener_modulos_por_rol(rol)
            empleado['info_rol'] = obtener_informacion_rol(rol)
            
            # Determinar módulos efectivos (personalizados o por rol)
            if empleado['tiene_permisos_personalizados']:
                empleado['modulos_efectivos'] = empleado['modulos_personalizados']
                empleado['tipo_permisos'] = 'PERSONALIZADOS'
            else:
                empleado['modulos_efectivos'] = [m['id'] for m in empleado['modulos_por_rol']]
                empleado['tipo_permisos'] = 'POR_ROL'
            
            empleado['total_modulos_efectivos'] = len(empleado['modulos_efectivos'])
        
        return empleados
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listando empleados con permisos: {str(e)}")

@router.post("/empleados/{email}/asignar-modulos", summary="Asignar módulos personalizados a empleado")
async def asignar_modulos_empleado(
    email: str,
    modulos: List[str],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Asigna módulos específicos a un empleado (sobrescribe permisos de rol)"""
    admin_email = (str(current_user.get("email") or current_user.get("sub") or "")).strip()
    if not admin_email:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    if not verificar_es_administrador(db, admin_email):
        raise HTTPException(status_code=403, detail="Acceso denegado: se requieren permisos de Administrador")
    
    try:
        resultado = asignar_modulos_personalizados(db, admin_email, email, modulos)
        return OperacionExitosaOut(mensaje=resultado["mensaje"], datos=resultado)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error asignando módulos: {str(e)}")

@router.delete("/empleados/{email}/permisos-personalizados", summary="Eliminar permisos personalizados")
async def eliminar_permisos_personalizados_empleado(
    email: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Elimina permisos personalizados y vuelve a usar permisos de rol"""
    admin_email = (str(current_user.get("email") or current_user.get("sub") or "")).strip()
    if not admin_email:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    if not verificar_es_administrador(db, admin_email):
        raise HTTPException(status_code=403, detail="Acceso denegado: se requieren permisos de Administrador")
    
    try:
        resultado = eliminar_permisos_personalizados(db, email)
        return OperacionExitosaOut(mensaje=resultado["mensaje"], datos=resultado)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error eliminando permisos personalizados: {str(e)}")

@router.get("/empleados/{email}/modulos-disponibles", summary="Ver módulos disponibles para empleado")
async def obtener_modulos_disponibles_empleado(
    email: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene módulos disponibles para un empleado específico"""
    admin_email = (str(current_user.get("email") or current_user.get("sub") or "")).strip()
    if not admin_email:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    if not verificar_es_administrador(db, admin_email):
        raise HTTPException(status_code=403, detail="Acceso denegado: se requieren permisos de Administrador")
    
    try:
        # Obtener información del empleado
        empleado = obtener_empleado(db, email)
        if not empleado:
            raise HTTPException(status_code=404, detail="Empleado no encontrado")
        
        rol = empleado.get('nomrol', 'Empleado')
        modulos_por_rol = obtener_modulos_por_rol(rol)
        modulos_personalizados = obtener_modulos_personalizados(db, email)
        
        # Determinar módulos activos
        if modulos_personalizados:
            modulos_activos = modulos_personalizados
        else:
            modulos_activos = modulos_por_rol
        
        return {
            "email": email,
            "rol": rol,
            "modulos_por_rol": modulos_por_rol,
            "modulos_personalizados": modulos_personalizados,
            "modulos_activos": modulos_activos,
            "tiene_permisos_personalizados": len(modulos_personalizados) > 0,
            "todos_los_modulos": obtener_modulos_disponibles()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo módulos: {str(e)}")