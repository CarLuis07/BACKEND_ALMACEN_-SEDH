from sqlalchemy.orm import Session
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

def login_empleado(db: Session, email: str, password: str) -> tuple[bool, str | None]:
    """
    Valida credenciales contra acceso.empleados_roles y obtiene el rol desde acceso.roles.
    Luego llama al procedimiento acceso.loginusuario para registrar UltimoLogin.
    Retorna (ok, rol).
    """
    try:
        row = db.execute(
            text(
                "SELECT r.nomrol AS rol "
                "FROM acceso.empleados_roles er "
                "JOIN acceso.roles r ON r.idrol = er.idrol "
                "WHERE LOWER(TRIM(er.emailinstitucional)) = LOWER(TRIM(:email)) "
                "AND er.contrasena = :pwd "
                "AND COALESCE(er.actlaboralmente, FALSE) = TRUE "
                "LIMIT 1"
            ),
            {"email": email, "pwd": password},
        ).mappings().first()

        if not row:
            db.rollback()
            return False, None

        rol = row["rol"]

        # Llamar al procedimiento (nombre en minúscula) para actualizar UltimoLogin.
        # OUT params no se usan aquí.
        try:
            db.execute(text("CALL acceso.loginusuario(:email, :pwd, NULL, NULL)"), {"email": email, "pwd": password})
            db.commit()
        except Exception as e:
            logger.warning("Procedimiento acceso.loginusuario falló, se continúa. Detalle: %s", e)
            db.rollback()

        return True, rol
    except Exception as e:
        logger.error("Error en login_empleado: %s", e)
        db.rollback()
        return False, None

def obtener_info_empleado(db: Session, email: str) -> dict | None:
    """
    Obtiene información completa del empleado por email.
    """
    try:
        row = db.execute(
            text(
                "SELECT "
                "er.emailinstitucional as email, "
                "COALESCE(e.nombre, 'Usuario') as nombre, "
                "r.nomrol as rol, "
                "COALESCE(d.nomdependencia, 'Sin dependencia') as dependencia "
                "FROM acceso.empleados_roles er "
                "JOIN acceso.roles r ON r.idrol = er.idrol "
                "LEFT JOIN usuarios.empleados e ON e.emailinstitucional = er.emailinstitucional "
                "LEFT JOIN usuarios.dependencias d ON d.iddependencia = e.iddependencia "
                "WHERE LOWER(TRIM(er.emailinstitucional)) = LOWER(TRIM(:email)) "
                "AND COALESCE(er.actlaboralmente, FALSE) = TRUE "
                "LIMIT 1"
            ),
            {"email": email},
        ).mappings().first()

        if not row:
            return None

        return {
            "email": row["email"],
            "nombre": row["nombre"],
            "rol": row["rol"],
            "dependencia": row["dependencia"]
        }
    except Exception as e:
        logger.error("Error en obtener_info_empleado: %s", e)
        return None


def obtener_roles_usuario(db: Session, email: str) -> list[dict]:
    """
    Obtiene todos los roles de un usuario usando la función almacenada.
    """
    try:
        result = db.execute(
            text("SELECT * FROM acceso.ObtenerRolesUsuario(:email)"),
            {"email": email}
        )
        
        roles = []
        for row in result.fetchall():
            roles.append({
                "email": row[0],
                "rol": row[1]
            })
        
        return roles
    except Exception as e:
        logger.error("Error en obtener_roles_usuario: %s", e)
        return []


def asignar_rol_usuario(db: Session, admin_email: str, usuario_email: str, id_rol: str) -> tuple[bool, str]:
    """
    Asigna un rol a un usuario usando el procedimiento almacenado.
    """
    try:
        # Ejecutar procedimiento almacenado
        result = db.execute(
            text("CALL acceso.AsignarRolUsuario(:admin_email, :usuario_email, :id_rol, '')"),
            {
                "admin_email": admin_email,
                "usuario_email": usuario_email,
                "id_rol": id_rol
            }
        )
        
        db.commit()
        return True, "Rol asignado exitosamente"
        
    except Exception as e:
        logger.error("Error en asignar_rol_usuario: %s", e)
        db.rollback()
        return False, f"Error al asignar rol: {str(e)}"


def asignar_modulo_rol(db: Session, admin_email: str, id_rol: str, modulo: str) -> tuple[bool, str]:
    """
    Asigna un módulo a un rol usando el procedimiento almacenado.
    """
    try:
        # Ejecutar procedimiento almacenado
        result = db.execute(
            text("CALL acceso.AsignarModuloARol(:admin_email, :id_rol, :modulo, '')"),
            {
                "admin_email": admin_email,
                "id_rol": id_rol,
                "modulo": modulo
            }
        )
        
        db.commit()
        return True, "Módulo asignado al rol exitosamente"
        
    except Exception as e:
        logger.error("Error en asignar_modulo_rol: %s", e)
        db.rollback()
        return False, f"Error al asignar módulo: {str(e)}"


def obtener_todos_roles(db: Session) -> list[dict]:
    """
    Obtiene todos los roles disponibles en el sistema.
    """
    try:
        result = db.execute(
            text("SELECT idrol, nomrol FROM acceso.roles ORDER BY nomrol")
        )
        
        roles = []
        for row in result.fetchall():
            roles.append({
                "id": str(row[0]),
                "nombre": row[1]
            })
        
        return roles
    except Exception as e:
        logger.error("Error en obtener_todos_roles: %s", e)
        return []


def obtener_modulos_rol(db: Session, id_rol: str) -> list[str]:
    """
    Obtiene todos los módulos asignados a un rol específico.
    """
    try:
        result = db.execute(
            text("SELECT modulo FROM acceso.roles_modulos WHERE idrol = :id_rol ORDER BY modulo"),
            {"id_rol": id_rol}
        )
        
        return [row[0] for row in result.fetchall()]
    except Exception as e:
        logger.error("Error en obtener_modulos_rol: %s", e)
        return []