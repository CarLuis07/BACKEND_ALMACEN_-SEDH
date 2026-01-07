-- Limpiar aprobaciones duplicadas de JefSerMat para UIT-001-2026
DELETE FROM requisiciones.aprobaciones
WHERE idrequisicion = (SELECT idrequisicion FROM requisiciones.requisiciones WHERE codrequisicion = 'UIT-001-2026')
AND rol = 'JefSerMat';

-- Verificar que se eliminaron
SELECT 'Aprobaciones después de limpiar:' as paso;
SELECT 
    r.codrequisicion,
    a.rol,
    a.estadoaprobacion
FROM requisiciones.aprobaciones a
JOIN requisiciones.requisiciones r ON r.idrequisicion = a.idrequisicion
WHERE r.codrequisicion = 'UIT-001-2026'
ORDER BY a.fecaprobacion;

-- Test completo: Llamar a la función con estados actualizados
SELECT '=== Total requisiciones pendientes para JefSerMat ===' as paso;
SELECT COUNT(*) as total
FROM requisiciones.requisiciones_pendientes_jefe_materiales('escarleth.nunez@sedh.gob.hn');

-- Ver las primeras 5
SELECT '=== Primeras 5 requisiciones ===' as paso;
SELECT codrequisicion, nombreempleado, fecsolicitud
FROM requisiciones.requisiciones_pendientes_jefe_materiales('escarleth.nunez@sedh.gob.hn')
ORDER BY fecsolicitud DESC
LIMIT 5;
