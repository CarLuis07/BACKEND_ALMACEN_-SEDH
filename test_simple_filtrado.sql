-- Test simplificado del filtrado de la función

-- Paso 1: Ver cuántas requisiciones hay ANTES de insertar aprobación de JefSerMat
SELECT '=== ANTES de aprobación JefSerMat ===' as paso;
SELECT COUNT(*) as total_antes
FROM requisiciones.requisiciones_pendientes_jefe_materiales('escarleth.nunez@sedh.gob.hn');

-- Ver si UIT-001-2026 está en la lista
SELECT codrequisicion
FROM requisiciones.requisiciones_pendientes_jefe_materiales('escarleth.nunez@sedh.gob.hn')
WHERE codrequisicion = 'UIT-001-2026';

-- Paso 2: Insertar aprobación de JefSerMat para UIT-001-2026
DO $$
DECLARE
    v_idrequisicion UUID;
    v_email TEXT := 'escarleth.nunez@sedh.gob.hn';
BEGIN
    -- Obtener el ID de la requisición
    SELECT idrequisicion INTO v_idrequisicion
    FROM requisiciones.requisiciones
    WHERE codrequisicion = 'UIT-001-2026';
    
    -- Insertar aprobación de JefSerMat
    INSERT INTO requisiciones.aprobaciones 
        (idrequisicion, emailinstitucional, rol, estadoaprobacion, comentario, fecaprobacion)
    VALUES 
        (v_idrequisicion, v_email, 'JefSerMat', 'APROBADO', 'Prueba de filtrado', CURRENT_DATE)
    ON CONFLICT DO NOTHING;
    
    RAISE NOTICE 'Aprobación de JefSerMat insertada para UIT-001-2026';
END $$;

-- Paso 3: Verificar que se insertó la aprobación
SELECT '=== Aprobaciones de UIT-001-2026 ===' as paso;
SELECT 
    a.rol,
    a.estadoaprobacion,
    a.fecaprobacion
FROM requisiciones.aprobaciones a
JOIN requisiciones.requisiciones r ON r.idrequisicion = a.idrequisicion
WHERE r.codrequisicion = 'UIT-001-2026'
ORDER BY a.fecaprobacion;

-- Paso 4: Ver cuántas requisiciones hay DESPUÉS de insertar aprobación
SELECT '=== DESPUÉS de aprobación JefSerMat ===' as paso;
SELECT COUNT(*) as total_despues
FROM requisiciones.requisiciones_pendientes_jefe_materiales('escarleth.nunez@sedh.gob.hn');

-- Verificar que UIT-001-2026 NO esté en la lista (debe estar vacío)
SELECT '=== UIT-001-2026 después (debe estar vacío) ===' as paso;
SELECT codrequisicion
FROM requisiciones.requisiciones_pendientes_jefe_materiales('escarleth.nunez@sedh.gob.hn')
WHERE codrequisicion = 'UIT-001-2026';
