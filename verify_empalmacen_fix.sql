-- Test: Verificar que UIT-001-2026 ahora aparezca en EmpAlmacen
SELECT '=== PENDIENTES EMPALMACEN (DESPUÉS DE FIX) ===' as paso;
SELECT codrequisicion, nombreempleado, fecsolicitud
FROM requisiciones.requisiciones_pendientes_almacen('maria.hernandez@sedh.gob.hn')
ORDER BY fecsolicitud DESC;

-- Verificar específicamente UIT-001-2026
SELECT '=== UIT-001-2026 en lista EmpAlmacen? ===' as paso;
SELECT codrequisicion
FROM requisiciones.requisiciones_pendientes_almacen('maria.hernandez@sedh.gob.hn')
WHERE codrequisicion = 'UIT-001-2026';
