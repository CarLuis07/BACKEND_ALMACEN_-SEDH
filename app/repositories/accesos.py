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