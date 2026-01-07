-- Paso 1: Verificar el estado actual de UIT-001-2026
SELECT 'Estado actual de UIT-001-2026:' as paso;
SELECT 
    r.codrequisicion,
    r.estgeneral,
    r.nomempleado
FROM requisiciones.requisiciones r
WHERE r.codrequisicion = 'UIT-001-2026';

-- Paso 2: Ver aprobaciones existentes para UIT-001-2026
SELECT 'Aprobaciones de UIT-001-2026:' as paso;
SELECT 
    a.rol,
    a.estadoaprobacion,
    a.fechora
FROM requisiciones.aprobaciones a
JOIN requisiciones.requisiciones r ON r.idrequisicion = a.idrequisicion
WHERE r.codrequisicion = 'UIT-001-2026'
ORDER BY a.fechora;

-- Paso 3: Llamar a la función ANTES de insertar aprobación de JefSerMat
SELECT 'Llamando función ANTES de aprobación JefSerMat:' as paso;
SELECT COUNT(*) as total_antes
FROM requisiciones.requisiciones_pendientes_jefe_materiales('escarleth.nunez@sedh.gob.hn');

-- Verificar si UIT-001-2026 está en la lista ANTES
SELECT 'UIT-001-2026 está en pendientes ANTES?' as paso;
SELECT codrequisicion
FROM requisiciones.requisiciones_pendientes_jefe_materiales('escarleth.nunez@sedh.gob.hn')
WHERE codrequisicion = 'UIT-001-2026';

-- Paso 4: Insertar aprobación de JefSerMat para UIT-001-2026
DO $$
DECLARE
    v_idrequisicion UUID;
BEGIN
    -- Obtener el ID de la requisición
    SELECT idrequisicion INTO v_idrequisicion
    FROM requisiciones.requisiciones
    WHERE codrequisicion = 'UIT-001-2026';
    
    -- Insertar aprobación de JefSerMat (si no existe)
    INSERT INTO requisiciones.aprobaciones 
        (idrequisicion, rol, estadoaprobacion, observacion, fechora)
    VALUES 
        (v_idrequisicion, 'JefSerMat', 'APROBADO', 'Prueba de filtrado', NOW())
    ON CONFLICT DO NOTHING;
    
    RAISE NOTICE 'Aprobación de JefSerMat insertada para UIT-001-2026';
END $$;

-- Paso 5: Verificar que se insertó
SELECT 'Verificando inserción:' as paso;
SELECT 
    a.rol,
    a.estadoaprobacion,
    a.observacion
FROM requisiciones.aprobaciones a
JOIN requisiciones.requisiciones r ON r.idrequisicion = a.idrequisicion
WHERE r.codrequisicion = 'UIT-001-2026'
ORDER BY a.fechora;

-- Paso 6: Llamar a la función DESPUÉS de insertar aprobación
SELECT 'Llamando función DESPUÉS de aprobación JefSerMat:' as paso;
SELECT COUNT(*) as total_despues
FROM requisiciones.requisiciones_pendientes_jefe_materiales('escarleth.nunez@sedh.gob.hn');

-- Verificar si UIT-001-2026 está en la lista DESPUÉS (NO DEBE ESTAR)
SELECT 'UIT-001-2026 está en pendientes DESPUÉS? (debe estar vacío)' as paso;
SELECT codrequisicion
FROM requisiciones.requisiciones_pendientes_jefe_materiales('escarleth.nunez@sedh.gob.hn')
WHERE codrequisicion = 'UIT-001-2026';
