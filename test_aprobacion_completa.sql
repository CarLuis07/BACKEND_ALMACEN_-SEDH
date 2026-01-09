-- Test completo de aprobación de UIT-001-2026

-- Paso 1: Limpiar cualquier aprobación anterior de JefSerMat
DELETE FROM requisiciones.aprobaciones
WHERE idrequisicion = (SELECT idrequisicion FROM requisiciones.requisiciones WHERE codrequisicion = 'UIT-001-2026')
AND rol = 'JefSerMat';

-- Paso 2: Verificar estado ANTES
SELECT '=== ANTES ===' as paso;
SELECT COUNT(*) as pendientes_jefsermat
FROM requisiciones.requisiciones_pendientes_jefe_materiales('escarleth.nunez@sedh.gob.hn');

SELECT 'UIT-001-2026 en lista?' as paso;
SELECT codrequisicion FROM requisiciones.requisiciones_pendientes_jefe_materiales('escarleth.nunez@sedh.gob.hn')
WHERE codrequisicion = 'UIT-001-2026';

-- Paso 3: Simular aprobación via función SQL
SELECT '=== APROBANDO ===' as paso;
SELECT requisiciones.responder_requisicion_jefe_materiales(
    (SELECT idrequisicion FROM requisiciones.requisiciones WHERE codrequisicion = 'UIT-001-2026'),
    'escarleth.nunez@sedh.gob.hn',
    'APROBADO',
    'Aprobada en test',
    '[]'::jsonb
);

-- Paso 4: Verificar aprobaciones insertadas
SELECT '=== APROBACIONES REGISTRADAS ===' as paso;
SELECT rol, estadoaprobacion, fecaprobacion
FROM requisiciones.aprobaciones
WHERE idrequisicion = (SELECT idrequisicion FROM requisiciones.requisiciones WHERE codrequisicion = 'UIT-001-2026')
ORDER BY fecaprobacion DESC;

-- Paso 5: Verificar si está en notificaciones del EmpAlmacen
SELECT '=== NOTIFICACIONES EMPALMACEN ===' as paso;
SELECT COUNT(*) as notificaciones
FROM requisiciones.notificaciones
WHERE idrequisicion = (SELECT idrequisicion FROM requisiciones.requisiciones WHERE codrequisicion = 'UIT-001-2026')
AND tipo = 'requisicion_pendiente';

-- Paso 6: Verificar estado DESPUÉS
SELECT '=== DESPUÉS ===' as paso;
SELECT COUNT(*) as pendientes_jefsermat
FROM requisiciones.requisiciones_pendientes_jefe_materiales('escarleth.nunez@sedh.gob.hn');

SELECT 'UIT-001-2026 en lista? (debe estar vacío)' as paso;
SELECT codrequisicion FROM requisiciones.requisiciones_pendientes_jefe_materiales('escarleth.nunez@sedh.gob.hn')
WHERE codrequisicion = 'UIT-001-2026';

-- Paso 7: Verificar que aparece en pendientes de EmpAlmacen
SELECT '=== PENDIENTES EMPALMACEN ===' as paso;
SELECT codrequisicion FROM requisiciones.requisiciones_pendientes_almacen('maria.hernandez@sedh.gob.hn')
WHERE codrequisicion = 'UIT-001-2026'
LIMIT 1;
