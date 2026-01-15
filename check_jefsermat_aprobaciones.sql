-- Verificar estado de aprobaciones JefSerMat para requisiciones pendientes
SELECT 
    r.codrequisicion,
    r.estgeneral,
    r.fecsolicitud,
    a.rol,
    a.estadoaprobacion,
    a.fecaprobacion,
    a.comentario
FROM requisiciones.requisiciones r
LEFT JOIN requisiciones.aprobaciones a ON r.idrequisicion = a.idrequisicion
WHERE r.codrequisicion IN ('UIT-003-2026', 'UIT-006-2026', 'UIT-004-2026')
ORDER BY r.codrequisicion, 
    CASE a.rol 
        WHEN 'JefInmediato' THEN 1 
        WHEN 'JefSerMat' THEN 2 
        WHEN 'EmpAlmacen' THEN 3 
        ELSE 4 
    END;

\echo ''
\echo '=== Verificar si aparecen para EmpAlmacen ==='
SELECT 
    COUNT(*) as total_pendientes_almacen
FROM requisiciones.requisiciones_pendientes_almacen('almacen@sedh.gob.hn');

\echo ''
\echo '=== Detalles de pendientes para EmpAlmacen ==='
SELECT 
    codrequisicion,
    nombreempleado,
    fecsolicitud,
    gastotaldelpedido
FROM requisiciones.requisiciones_pendientes_almacen('almacen@sedh.gob.hn')
ORDER BY fecsolicitud DESC;
