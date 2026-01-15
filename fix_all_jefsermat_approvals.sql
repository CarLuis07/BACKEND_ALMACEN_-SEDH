-- SANEO GLOBAL: Insertar aprobaciones JefSerMat faltantes
-- Para requisiciones EN ESPERA que fueron "aprobadas" pero no tienen el registro

-- 1. Ver cuántas requisiciones EN ESPERA no tienen aprobación JefSerMat
SELECT COUNT(*) AS requisiciones_sin_jefsermat
FROM requisiciones.requisiciones r
WHERE r.estgeneral = 'EN ESPERA'
  AND r.actualizadopor IS NOT NULL
  AND EXISTS (
      SELECT 1 FROM acceso.empleados_roles er
      JOIN acceso.roles ro ON ro.idrol = er.idrol
      WHERE er.emailinstitucional = r.actualizadopor
        AND ro.nomrol = 'JefSerMat'
        AND er.actlaboralmente = TRUE
  )
  AND NOT EXISTS (
      SELECT 1 FROM requisiciones.aprobaciones a
      WHERE a.idrequisicion = r.idrequisicion
        AND a.rol = 'JefSerMat'
  );

-- 2. Listar códigos afectados (máximo 50)
SELECT r.codrequisicion, r.actualizadopor, r.actualizadoen
FROM requisiciones.requisiciones r
WHERE r.estgeneral = 'EN ESPERA'
  AND r.actualizadopor IS NOT NULL
  AND EXISTS (
      SELECT 1 FROM acceso.empleados_roles er
      JOIN acceso.roles ro ON ro.idrol = er.idrol
      WHERE er.emailinstitucional = r.actualizadopor
        AND ro.nomrol = 'JefSerMat'
        AND er.actlaboralmente = TRUE
  )
  AND NOT EXISTS (
      SELECT 1 FROM requisiciones.aprobaciones a
      WHERE a.idrequisicion = r.idrequisicion
        AND a.rol = 'JefSerMat'
  )
ORDER BY r.fecsolicitud DESC
LIMIT 50;

-- 3. Insertar aprobaciones faltantes
INSERT INTO requisiciones.aprobaciones (
    idaprobacion, idrequisicion, emailinstitucional, rol, estadoaprobacion, comentario, fecaprobacion
)
SELECT 
    uuid_generate_v4(),
    r.idrequisicion,
    r.actualizadopor,
    'JefSerMat',
    'APROBADO',
    'Backfill aprobación JefSerMat',
    COALESCE(r.actualizadoen::date, CURRENT_DATE)
FROM requisiciones.requisiciones r
WHERE r.estgeneral = 'EN ESPERA'
  AND r.actualizadopor IS NOT NULL
  AND EXISTS (
      SELECT 1 FROM acceso.empleados_roles er
      JOIN acceso.roles ro ON ro.idrol = er.idrol
      WHERE er.emailinstitucional = r.actualizadopor
        AND ro.nomrol = 'JefSerMat'
        AND er.actlaboralmente = TRUE
  )
  AND NOT EXISTS (
      SELECT 1 FROM requisiciones.aprobaciones a
      WHERE a.idrequisicion = r.idrequisicion
        AND a.rol = 'JefSerMat'
  );

-- 4. Verificar códigos afectados por el backfill
SELECT r.codrequisicion, a.emailinstitucional, a.estadoaprobacion, a.fecaprobacion
FROM requisiciones.aprobaciones a
JOIN requisiciones.requisiciones r ON r.idrequisicion = a.idrequisicion
WHERE a.comentario = 'Backfill aprobación JefSerMat'
ORDER BY r.fecsolicitud DESC;

-- 5. Verificar que ahora aparezcan en pendientes de almacén
SELECT COUNT(*) AS total_pendientes_almacen
FROM requisiciones.requisiciones_pendientes_almacen('maria.hernandez@sedh.gob.hn');

SELECT codrequisicion, nombreempleado, fecsolicitud
FROM requisiciones.requisiciones_pendientes_almacen('maria.hernandez@sedh.gob.hn')
ORDER BY fecsolicitud DESC
LIMIT 20;
