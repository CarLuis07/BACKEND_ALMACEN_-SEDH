-- Test: Aprobar UIT-001-2026 como JefSerMat y verificar que desaparezca
SELECT '=== ANTES de aprobar ===' as paso;
SELECT COUNT(*) as total_antes
FROM requisiciones.requisiciones_pendientes_jefe_materiales('escarleth.nunez@sedh.gob.hn');

-- Verificar que UIT-001-2026 esté en la lista
SELECT codrequisicion
FROM requisiciones.requisiciones_pendientes_jefe_materiales('escarleth.nunez@sedh.gob.hn')
WHERE codrequisicion = 'UIT-001-2026';

-- Insertar aprobación de JefSerMat
INSERT INTO requisiciones.aprobaciones 
    (idrequisicion, emailinstitucional, rol, estadoaprobacion, comentario, fecaprobacion)
VALUES 
    (
        (SELECT idrequisicion FROM requisiciones.requisiciones WHERE codrequisicion = 'UIT-001-2026'),
        'escarleth.nunez@sedh.gob.hn',
        'JefSerMat',
        'APROBADO',
        'Aprobado por JefSerMat - Test filtrado',
        CURRENT_DATE
    );

SELECT '=== DESPUÉS de aprobar ===' as paso;
SELECT COUNT(*) as total_despues
FROM requisiciones.requisiciones_pendientes_jefe_materiales('escarleth.nunez@sedh.gob.hn');

-- Verificar que UIT-001-2026 NO esté en la lista (debe estar vacío)
SELECT 'UIT-001-2026 en lista después (debe estar vacío):' as paso;
SELECT codrequisicion
FROM requisiciones.requisiciones_pendientes_jefe_materiales('escarleth.nunez@sedh.gob.hn')
WHERE codrequisicion = 'UIT-001-2026';
