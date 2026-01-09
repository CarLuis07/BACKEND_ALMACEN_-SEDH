-- Test completo de aprobación con UIT-001-2026 en estado EN ESPERA

-- Paso 1: Verificar estado ANTES
SELECT '=== ANTES DE APROBACIÓN ===' as paso;
SELECT COUNT(*) as total_pendientes_jefsermat
FROM requisiciones.requisiciones_pendientes_jefe_materiales('escarleth.nunez@sedh.gob.hn');

SELECT 'UIT-001-2026 en pendientes?' as paso;
SELECT codrequisicion FROM requisiciones.requisiciones_pendientes_jefe_materiales('escarleth.nunez@sedh.gob.hn')
WHERE codrequisicion = 'UIT-001-2026';

-- Paso 2: Simular aprobación
SELECT '=== APROBANDO VÍA FUNCIÓN SQL ===' as paso;
SELECT requisiciones.responder_requisicion_jefe_materiales(
    (SELECT idrequisicion FROM requisiciones.requisiciones WHERE codrequisicion = 'UIT-001-2026'),
    'escarleth.nunez@sedh.gob.hn'::text,
    'APROBADO'::text,
    'Aprobada en test'::text,
    '[]'::text
) as resultado;

-- Paso 3: Verificar aprobaciones insertadas
SELECT '=== APROBACIONES REGISTRADAS ===' as paso;
SELECT rol, estadoaprobacion, fecaprobacion
FROM requisiciones.aprobaciones
WHERE idrequisicion = (SELECT idrequisicion FROM requisiciones.requisiciones WHERE codrequisicion = 'UIT-001-2026')
ORDER BY fecaprobacion DESC;

-- Paso 4: Verificar estado DESPUÉS
SELECT '=== DESPUÉS DE APROBACIÓN ===' as paso;
SELECT COUNT(*) as total_pendientes_jefsermat
FROM requisiciones.requisiciones_pendientes_jefe_materiales('escarleth.nunez@sedh.gob.hn');

SELECT 'UIT-001-2026 en pendientes? (debe estar vacío)' as paso;
SELECT codrequisicion FROM requisiciones.requisiciones_pendientes_jefe_materiales('escarleth.nunez@sedh.gob.hn')
WHERE codrequisicion = 'UIT-001-2026';

-- Paso 5: Verificar si EmpAlmacen lo ve
SELECT '=== PENDIENTES EMPALMACEN ===' as paso;
SELECT codrequisicion FROM requisiciones.requisiciones_pendientes_almacen('maria.hernandez@sedh.gob.hn')
WHERE codrequisicion = 'UIT-001-2026'
LIMIT 1;
