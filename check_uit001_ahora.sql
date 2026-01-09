-- Ver estado actual completo de UIT-001-2026
SELECT '=== APROBACIONES ACTUALES UIT-001-2026 ===' as paso;
SELECT 
    rol,
    estadoaprobacion,
    emailinstitucional,
    comentario,
    fecaprobacion
FROM requisiciones.aprobaciones
WHERE idrequisicion = (SELECT idrequisicion FROM requisiciones.requisiciones WHERE codrequisicion = 'UIT-001-2026')
ORDER BY fecaprobacion DESC NULLS LAST;

-- Estado general
SELECT 'Estado requisicion:' as info, estgeneral 
FROM requisiciones.requisiciones 
WHERE codrequisicion = 'UIT-001-2026';

-- ¿Aparece en lista EmpAlmacen ahora?
SELECT '=== ¿APARECE EN EMPALMACEN AHORA? ===' as paso;
SELECT COUNT(*) as total
FROM requisiciones.requisiciones_pendientes_almacen('maria.hernandez@sedh.gob.hn')
WHERE codrequisicion = 'UIT-001-2026';
