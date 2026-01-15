BEGIN;

-- Vista previa: cuántas requisiciones EN ESPERA no tienen aprobación JefSerMat
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

-- Insertar aprobaciones faltantes
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

-- Mostrar qué códigos fueron afectados por el saneo
SELECT r.codrequisicion, a.rol, a.estadoaprobacion, a.emailinstitucional
FROM requisiciones.aprobaciones a
JOIN requisiciones.requisiciones r ON r.idrequisicion = a.idrequisicion
WHERE a.comentario = 'Backfill por saneo'
ORDER BY r.fecsolicitud;

COMMIT;
