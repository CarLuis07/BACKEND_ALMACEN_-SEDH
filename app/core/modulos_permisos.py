"""
Sistema de permisos y módulos del sistema
Configuración completa de qué rol puede ver qué módulos
"""
from typing import Dict, List

# Definición de módulos del sistema
MODULOS_SISTEMA = {
    "dashboard": {
        "nombre": "Dashboard Principal",
        "descripcion": "Panel principal del sistema",
        "url": "/dashboard",
        "icono": "🏠"
    },
    "productos": {
        "nombre": "Gestión de Productos",
        "descripcion": "Ver, crear y editar productos del inventario",
        "url": "/productos",
        "icono": "📦"
    },
    "categorias": {
        "nombre": "Gestión de Categorías",
        "descripcion": "Ver y gestionar categorías de productos",
        "url": "/categorias", 
        "icono": "🏷️"
    },
    "agregar_producto": {
        "nombre": "Agregar Producto",
        "descripcion": "Registrar nuevos productos en el inventario",
        "url": "#",
        "icono": "➕",
        "accion": "modal"
    },
    "requisiciones": {
        "nombre": "Requisiciones",
        "descripcion": "Crear y gestionar solicitudes de materiales",
        "url": "/requisiciones",
        "icono": "📋"
    },
    "mis_requisiciones": {
        "nombre": "Mis Requisiciones",
        "descripcion": "Ver mis solicitudes personales",
        "url": "/mis-requisiciones",
        "icono": "📊"
    },
    "movimientos": {
        "nombre": "Movimientos de Inventario",
        "descripcion": "Control de entradas y salidas del almacén",
        "url": "/movimientos",
        "icono": "🔄"
    },
    "accesos": {
        "nombre": "Gestión de Accesos",
        "descripcion": "Administración básica de usuarios",
        "url": "/accesos",
        "icono": "👥"
    },
    "administracion": {
        "nombre": "Panel de Administración",
        "descripcion": "Control total del sistema: empleados, roles, permisos",
        "url": "/admin",
        "icono": "⚙️"
    },
    "reportes": {
        "nombre": "Reportes y Estadísticas",
        "descripcion": "Informes del sistema y métricas",
        "url": "/reportes",
        "icono": "📈"
    },
    "auditoria": {
        "nombre": "Auditoría del Sistema",
        "descripcion": "Logs y seguimiento de actividades",
        "url": "/auditoria",
        "icono": "🔍"
    },
    "reportes_completo": {
        "nombre": "Reportes Completos",
        "descripcion": "Análisis detallado de requisiciones con flujos de aprobación completos",
        "url": "/reportes-completo",
        "icono": "📋"
    },
    # Módulos del Sistema Avanzado de Movimientos
    "movimientos_dashboard": {
        "nombre": "Dashboard de Movimientos",
        "descripcion": "Analytics interactivo con gráficas y métricas en tiempo real",
        "url": "/movimientos-dashboard",
        "icono": "📊"
    },
    "movimientos_trazabilidad": {
        "nombre": "Trazabilidad de Productos",
        "descripcion": "Seguimiento detallado con código de barras y timeline de movimientos",
        "url": "/movimientos-trazabilidad",
        "icono": "🔍"
    },
    "movimientos_alertas": {
        "nombre": "Sistema de Alertas",
        "descripcion": "Notificaciones inteligentes de stock, vencimientos y sugerencias automáticas",
        "url": "/movimientos-alertas",
        "icono": "🚨"
    },
    "movimientos_inventario": {
        "nombre": "Inventario Físico",
        "descripcion": "Conteos cíclicos, conciliación automática y reportes de discrepancias",
        "url": "/movimientos-inventario",
        "icono": "📋"
    }
}

# Permisos por rol - Define qué módulos puede ver cada rol
PERMISOS_POR_ROL = {
    "Administrador": {
        "modulos": [
            "dashboard",
            "productos", 
            "categorias",
            "agregar_producto",
            "requisiciones",
            "mis_requisiciones", 
            "movimientos",
            "accesos",
            "administracion",
            "reportes",
            "auditoria",
            "reportes_completo",
            "movimientos_dashboard",
            "movimientos_trazabilidad",
            "movimientos_alertas",
            "movimientos_inventario"
        ],
        "descripcion": "Acceso completo a todos los módulos del sistema",
        "nivel_acceso": "TOTAL"
    },
    "EmpAlmacen": {
        "modulos": [
            "dashboard",
            "productos",
            "categorias", 
            "agregar_producto",
            "requisiciones",
            "mis_requisiciones",
            "movimientos",
            "movimientos_dashboard",
            "movimientos_trazabilidad",
            "movimientos_alertas",
            "movimientos_inventario"
        ],
        "descripcion": "Gestión completa del almacén y productos",
        "nivel_acceso": "ALMACEN"
    },
    "JefSerMat": {
        "modulos": [
            "dashboard",
            "productos",
            "categorias",
            "requisiciones",
            "mis_requisiciones",
            "movimientos", 
            "reportes",
            "reportes_completo",
            "movimientos_dashboard",
            "movimientos_trazabilidad",
            "movimientos_alertas",
            "movimientos_inventario"
        ],
        "descripcion": "Supervisión de materiales y aprobaciones",
        "nivel_acceso": "JEFATURA"
    },
    "GerAdmon": {
        "modulos": [
            "dashboard",
            "productos",
            "categorias",
            "requisiciones", 
            "mis_requisiciones",
            "reportes",
            "reportes_completo"
        ],
        "descripcion": "Gestión administrativa y aprobaciones gerenciales",
        "nivel_acceso": "GERENCIAL"
    },
    "JefInmediato": {
        "modulos": [
            "dashboard",
            "productos",
            "categorias",
            "requisiciones",
            "mis_requisiciones"
        ],
        "descripcion": "Aprobación de requisiciones de su equipo",
        "nivel_acceso": "SUPERVISOR"
    },
    "Empleado": {
        "modulos": [
            "dashboard",
            "productos",
            "categorias",
            "requisiciones",
            "mis_requisiciones"
        ],
        "descripcion": "Operaciones básicas de empleado",
        "nivel_acceso": "BASICO"
    },
    "Auditor": {
        "modulos": [
            "dashboard",
            "productos", 
            "categorias",
            "requisiciones",
            "movimientos",
            "reportes",
            "auditoria",
            "reportes_completo"
        ],
        "descripcion": "Acceso de solo lectura para auditorías",
        "nivel_acceso": "AUDITORIA"
    }
}

def obtener_modulos_por_rol(rol: str) -> List[Dict]:
    """
    Obtiene la lista de módulos disponibles para un rol específico
    """
    if rol not in PERMISOS_POR_ROL:
        return []
    
    modulos_permitidos = PERMISOS_POR_ROL[rol]["modulos"]
    modulos_disponibles = []
    
    for modulo_id in modulos_permitidos:
        if modulo_id in MODULOS_SISTEMA:
            modulo_info = MODULOS_SISTEMA[modulo_id].copy()
            modulo_info["id"] = modulo_id
            modulos_disponibles.append(modulo_info)
    
    return modulos_disponibles

def verificar_acceso_modulo(rol: str, modulo: str) -> bool:
    """
    Verifica si un rol tiene acceso a un módulo específico
    """
    if rol not in PERMISOS_POR_ROL:
        return False
    
    return modulo in PERMISOS_POR_ROL[rol]["modulos"]

def obtener_informacion_rol(rol: str) -> Dict:
    """
    Obtiene información completa de un rol
    """
    if rol not in PERMISOS_POR_ROL:
        return {
            "descripcion": "Rol no definido",
            "nivel_acceso": "NINGUNO",
            "modulos": [],
            "total_modulos": 0
        }
    
    info_rol = PERMISOS_POR_ROL[rol].copy()
    info_rol["total_modulos"] = len(info_rol["modulos"])
    
    return info_rol

def obtener_todos_los_roles() -> Dict:
    """
    Obtiene información de todos los roles disponibles
    """
    return PERMISOS_POR_ROL

def obtener_modulos_disponibles() -> Dict:
    """
    Obtiene todos los módulos disponibles en el sistema
    """
    return MODULOS_SISTEMA

def generar_matriz_permisos() -> List[Dict]:
    """
    Genera una matriz de permisos rol x módulo para visualización administrativa
    """
    matriz = []
    
    for rol, info_rol in PERMISOS_POR_ROL.items():
        for modulo_id, modulo_info in MODULOS_SISTEMA.items():
            matriz.append({
                "rol": rol,
                "modulo": modulo_id,
                "modulo_nombre": modulo_info["nombre"],
                "tiene_acceso": modulo_id in info_rol["modulos"],
                "nivel_acceso": info_rol["nivel_acceso"]
            })
    
    return matriz