-- Verificar estado de UIT-004-2026 después de la aprobación
SELECT 
    r.codrequisicion,
    r.estgeneral,
    r.gastotaldelpedido,
    a.rol,
    a.estadoaprobacion,
    a.emailinstitucional,
    a.fecaprobacion
FROM requisiciones.requisiciones r
LEFT JOIN requisiciones.aprobaciones a ON r.idrequisicion = a.idrequisicion
WHERE r.codrequisicion = 'UIT-004-2026'
ORDER BY 
    CASE a.rol 
        WHEN 'JefInmediato' THEN 1 
        WHEN 'JefSerMat' THEN 2 
        WHEN 'EmpAlmacen' THEN 3 
        ELSE 4 
    END;

\echo ''
\echo '=== Verificar si ahora aparece para EmpAlmacen ==='
SELECT COUNT(*) as aparece_para_almacen
FROM requisiciones.requisiciones_pendientes_almacen('almacen@sedh.gob.hn')
WHERE codrequisicion = 'UIT-004-2026';

\echo ''
\echo '=== Ver todas las requisiciones pendientes para EmpAlmacen ==='
SELECT codrequisicion, nombreempleado, fecsolicitud, gastotaldelpedido
FROM requisiciones.requisiciones_pendientes_almacen('almacen@sedh.gob.hn')
ORDER BY fecsolicitud DESC;
