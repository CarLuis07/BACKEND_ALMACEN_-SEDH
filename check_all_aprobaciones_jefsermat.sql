-- Verificar TODAS las aprobaciones de JefSerMat para estas requisiciones
SELECT 
    r.codrequisicion,
    r.estgeneral,
    a.rol,
    a.estadoaprobacion,
    a.emailinstitucional,
    a.fecaprobacion
FROM requisiciones.requisiciones r
LEFT JOIN requisiciones.aprobaciones a ON r.idrequisicion = a.idrequisicion
WHERE r.codrequisicion IN ('UIT-003-2026', 'UIT-004-2026', 'UIT-006-2026')
ORDER BY r.codrequisicion, a.rol;

\echo ''
\echo '=== Solo aprobaciones de JefSerMat ==='
SELECT 
    r.codrequisicion,
    a.estadoaprobacion,
    a.emailinstitucional,
    a.fecaprobacion,
    a.comentario
FROM requisiciones.requisiciones r
INNER JOIN requisiciones.aprobaciones a ON r.idrequisicion = a.idrequisicion
WHERE r.codrequisicion IN ('UIT-003-2026', 'UIT-004-2026', 'UIT-006-2026')
  AND a.rol = 'JefSerMat'
ORDER BY r.codrequisicion;
