-- Test: Verificar que la función actualizada funciona correctamente

-- 1. Ver todas las requisiciones EN ESPERA actuales
SELECT r.codrequisicion, r.estgeneral, r.actualizadopor,
       COUNT(a.idaprobacion) FILTER (WHERE a.rol = 'JefSerMat') as aprobaciones_jefsermat,
       COUNT(a.idaprobacion) FILTER (WHERE a.rol = 'EmpAlmacen' AND a.estadoaprobacion IN ('APROBADO','RECHAZADO')) as procesadas_almacen
FROM requisiciones.requisiciones r
LEFT JOIN requisiciones.aprobaciones a ON a.idrequisicion = r.idrequisicion
WHERE r.estgeneral = 'EN ESPERA'
GROUP BY r.codrequisicion, r.estgeneral, r.actualizadopor
ORDER BY r.fecsolicitud DESC;

-- 2. Ver cuántas aparecen en pendientes de almacén
SELECT COUNT(*) as total_pendientes_almacen
FROM requisiciones.requisiciones_pendientes_almacen('maria.hernandez@sedh.gob.hn');

-- 3. Listar las pendientes con detalles
SELECT codrequisicion, nombreempleado, fecsolicitud, gastotaldelpedido
FROM requisiciones.requisiciones_pendientes_almacen('maria.hernandez@sedh.gob.hn')
ORDER BY fecsolicitud DESC;
