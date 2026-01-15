-- Ver si se insertó el registro de JefSerMat en aprobaciones
SELECT 
    'APROBACIONES DE UIT-064-2025:' as debug,
    a.rol,
    a.estadoaprobacion,
    a.fecaprobacion
FROM requisiciones.aprobaciones a
WHERE a.idrequisicion = 'd007d546-3415-4d63-9aa3-ed1e3b507957'
ORDER BY a.fecaprobacion DESC;
