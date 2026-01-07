-- Ver estados de todas las requisiciones que deberían estar en pendientes de JefSerMat
SELECT 
    r.codrequisicion,
    r.estgeneral,
    r.nomempleado,
    COUNT(a.idaprobacion) FILTER (WHERE a.rol = 'JefSerMat') as aprobaciones_jefsermat
FROM requisiciones.requisiciones r
LEFT JOIN requisiciones.aprobaciones a ON a.idrequisicion = r.idrequisicion
GROUP BY r.idrequisicion, r.codrequisicion, r.estgeneral, r.nomempleado
HAVING COUNT(a.idaprobacion) FILTER (WHERE a.rol = 'JefSerMat') = 0
ORDER BY r.fecsolicitud DESC
LIMIT 10;

-- Ver requisiciones con aprobación JefInmediato pero sin JefSerMat
SELECT 
    r.codrequisicion,
    r.estgeneral,
    r.nomempleado
FROM requisiciones.requisiciones r
WHERE EXISTS (
    SELECT 1 FROM requisiciones.aprobaciones a 
    WHERE a.idrequisicion = r.idrequisicion 
    AND a.rol = 'JefInmediato' 
    AND a.estadoaprobacion = 'APROBADO'
)
AND NOT EXISTS (
    SELECT 1 FROM requisiciones.aprobaciones a 
    WHERE a.idrequisicion = r.idrequisicion 
    AND a.rol = 'JefSerMat'
)
ORDER BY r.fecsolicitud DESC;
