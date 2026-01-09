-- Verificar aprobaciones de UIT-001-2026
SELECT '=== APROBACIONES DE UIT-001-2026 ===' as paso;
SELECT 
    rol,
    estadoaprobacion,
    emailinstitucional,
    fecaprobacion,
    comentario
FROM requisiciones.aprobaciones
WHERE idrequisicion = (SELECT idrequisicion FROM requisiciones.requisiciones WHERE codrequisicion = 'UIT-001-2026')
ORDER BY fecaprobacion DESC;

-- Verificar estado general
SELECT '=== ESTADO GENERAL ===' as paso;
SELECT 
    codrequisicion,
    estgeneral,
    nomempleado
FROM requisiciones.requisiciones
WHERE codrequisicion = 'UIT-001-2026';

-- Verificar qué ve EmpAlmacen
SELECT '=== LO QUE VE EMPALMACEN ===' as paso;
SELECT codrequisicion, nombreempleado, fecsolicitud
FROM requisiciones.requisiciones_pendientes_almacen('maria.hernandez@sedh.gob.hn')
ORDER BY fecsolicitud DESC
LIMIT 5;

-- Ver definición de función pendientes almacén
SELECT '=== FUNCIÓN PENDIENTES ALMACÉN ===' as paso;
SELECT pg_get_functiondef(oid)
FROM pg_proc
WHERE proname = 'requisiciones_pendientes_almacen'
AND pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'requisiciones');
