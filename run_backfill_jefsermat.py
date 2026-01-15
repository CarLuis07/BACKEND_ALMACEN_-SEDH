import argparse
from sqlalchemy import text
from app.core.database import engine

PREVIEW_COUNT_SQL = text(
    """
    SELECT COUNT(*) AS faltantes
    FROM requisiciones.requisiciones r
    WHERE r.estgeneral = 'EN ESPERA'
      AND r.actualizadopor IS NOT NULL
      AND EXISTS (
          SELECT 1
          FROM acceso.empleados_roles er
          JOIN acceso.roles ro ON ro.idrol = er.idrol
          WHERE er.emailinstitucional = r.actualizadopor
            AND ro.nomrol = 'JefSerMat'
            AND er.actlaboralmente = TRUE
      )
      AND NOT EXISTS (
          SELECT 1
          FROM requisiciones.aprobaciones a
          WHERE a.idrequisicion = r.idrequisicion
            AND a.rol = 'JefSerMat'
      );
    """
)

PREVIEW_LIST_SQL = text(
    """
    SELECT r.codrequisicion
    FROM requisiciones.requisiciones r
    WHERE r.estgeneral = 'EN ESPERA'
      AND r.actualizadopor IS NOT NULL
      AND EXISTS (
          SELECT 1
          FROM acceso.empleados_roles er
          JOIN acceso.roles ro ON ro.idrol = er.idrol
          WHERE er.emailinstitucional = r.actualizadopor
            AND ro.nomrol = 'JefSerMat'
            AND er.actlaboralmente = TRUE
      )
      AND NOT EXISTS (
          SELECT 1
          FROM requisiciones.aprobaciones a
          WHERE a.idrequisicion = r.idrequisicion
            AND a.rol = 'JefSerMat'
      )
    ORDER BY r.fecsolicitud
    LIMIT 50;
    """
)

INSERT_SQL = text(
    """
    INSERT INTO requisiciones.aprobaciones (
        idaprobacion, idrequisicion, emailinstitucional, rol, estadoaprobacion, comentario, fecaprobacion
    )
    SELECT 
        uuid_generate_v4(),
        r.idrequisicion,
        r.actualizadopor,
        'JefSerMat',
        'APROBADO',
        'Backfill por saneo',
        COALESCE(r.actualizadoen::date, CURRENT_DATE)
    FROM requisiciones.requisiciones r
    WHERE r.estgeneral = 'EN ESPERA'
      AND r.actualizadopor IS NOT NULL
      AND EXISTS (
          SELECT 1
          FROM acceso.empleados_roles er
          JOIN acceso.roles ro ON ro.idrol = er.idrol
          WHERE er.emailinstitucional = r.actualizadopor
            AND ro.nomrol = 'JefSerMat'
            AND er.actlaboralmente = TRUE
      )
      AND NOT EXISTS (
          SELECT 1
          FROM requisiciones.aprobaciones a
          WHERE a.idrequisicion = r.idrequisicion
            AND a.rol = 'JefSerMat'
      );
    """
)

AFFECTED_TODAY_SQL = text(
    """
    SELECT r.codrequisicion, a.rol, a.estadoaprobacion, a.emailinstitucional, a.fecaprobacion
    FROM requisiciones.aprobaciones a
    JOIN requisiciones.requisiciones r ON r.idrequisicion = a.idrequisicion
    WHERE a.comentario = 'Backfill por saneo'
      AND a.fecaprobacion::date = CURRENT_DATE
    ORDER BY r.fecsolicitud;
    """
)


def run(dry_run: bool):
    with engine.connect() as conn:
        if dry_run:
            faltantes = conn.execute(PREVIEW_COUNT_SQL).scalar_one()
            print(f"Candidatos faltantes (EN ESPERA sin aprobación JefSerMat): {faltantes}")
            print("Ejemplos (máx 50):")
            for (cod,) in conn.execute(PREVIEW_LIST_SQL).all():
                print(f" - {cod}")
            return

        trans = conn.begin()
        try:
            result = conn.execute(INSERT_SQL)
            print(f"Aprobaciones insertadas: {result.rowcount}")
            print("Afectados hoy:")
            rows = conn.execute(AFFECTED_TODAY_SQL).all()
            for cod, rol, estado, email, fecha in rows:
                print(f" - {cod} | {rol}={estado} | {email} | {fecha}")
            trans.commit()
        except Exception as e:
            trans.rollback()
            print("Error durante el saneo:", e)
            raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backfill de aprobaciones JefSerMat para requisiciones EN ESPERA")
    parser.add_argument("--dry-run", action="store_true", help="Solo mostrar conteo y ejemplos, sin insertar")
    args = parser.parse_args()
    run(dry_run=args.dry_run)
