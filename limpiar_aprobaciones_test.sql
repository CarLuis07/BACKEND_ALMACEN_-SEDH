-- Eliminar las aprobaciones de JefSerMat que inserté manualmente
DELETE FROM requisiciones.aprobaciones
WHERE idrequisicion IN (
    SELECT idrequisicion FROM requisiciones.requisiciones
    WHERE codrequisicion IN ('UIT-003-2026', 'UIT-004-2026', 'UIT-006-2026')
)
AND rol = 'JefSerMat';

\echo '=== Aprobaciones eliminadas ==='
\echo ''

-- Verificar que ya no existen
SELECT 
    r.codrequisicion,
    a.rol,
    a.estadoaprobacion
FROM requisiciones.requisiciones r
LEFT JOIN requisiciones.aprobaciones a ON r.idrequisicion = a.idrequisicion
WHERE r.codrequisicion IN ('UIT-003-2026', 'UIT-004-2026', 'UIT-006-2026')
ORDER BY r.codrequisicion, a.rol;
