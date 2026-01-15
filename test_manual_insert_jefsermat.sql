-- Primero, obtener el UUID de la requisición UIT-003-2026
DO $$
DECLARE
    v_id_requisicion UUID;
BEGIN
    SELECT idrequisicion INTO v_id_requisicion
    FROM requisiciones.requisiciones
    WHERE codrequisicion = 'UIT-003-2026';

    RAISE NOTICE 'ID de UIT-003-2026: %', v_id_requisicion;

    -- Verificar si ya existe aprobación de JefSerMat
    IF EXISTS (
        SELECT 1 FROM requisiciones.aprobaciones
        WHERE idrequisicion = v_id_requisicion
          AND rol = 'JefSerMat'
          AND estadoaprobacion = 'APROBADO'
    ) THEN
        RAISE NOTICE 'Ya existe aprobación de JefSerMat APROBADO para esta requisición';
    ELSE
        RAISE NOTICE 'NO existe aprobación de JefSerMat APROBADO - se debería insertar';
    END IF;
END $$;

\echo ''
\echo '=== Probando INSERT manual ==='
-- Intentar insertar manualmente una aprobación de JefSerMat
INSERT INTO requisiciones.aprobaciones (
    idaprobacion,
    idrequisicion,
    emailinstitucional,
    rol,
    estadoaprobacion,
    comentario,
    fecaprobacion
)
SELECT
    uuid_generate_v4(),
    idrequisicion,
    'escarleth.ortiz@sedh.gob.hn',
    'JefSerMat',
    'APROBADO',
    'Prueba manual de inserción',
    CURRENT_DATE
FROM requisiciones.requisiciones
WHERE codrequisicion = 'UIT-003-2026'
  AND NOT EXISTS (
    SELECT 1 FROM requisiciones.aprobaciones
    WHERE idrequisicion = requisiciones.requisiciones.idrequisicion
      AND rol = 'JefSerMat'
      AND estadoaprobacion = 'APROBADO'
);

\echo ''
\echo '=== Verificar si se insertó ==='
SELECT 
    r.codrequisicion,
    a.rol,
    a.estadoaprobacion,
    a.emailinstitucional,
    a.fecaprobacion
FROM requisiciones.requisiciones r
INNER JOIN requisiciones.aprobaciones a ON r.idrequisicion = a.idrequisicion
WHERE r.codrequisicion = 'UIT-003-2026'
  AND a.rol = 'JefSerMat';
