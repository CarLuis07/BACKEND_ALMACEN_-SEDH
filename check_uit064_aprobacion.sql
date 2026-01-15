-- Verificar si la aprobación de UIT-064-2025 se creó
-- UUID: d007d546-3415-4d63-9aa3-ed1e3b507957

SELECT 
    'APROBACIONES PARA UIT-064-2025:' as debug,
    a.idrequisicion,
    a.rol,
    a.estadoaprobacion,
    a.fecaprobacion,
    a.comentario
FROM requisiciones.aprobaciones a
WHERE a.idrequisicion = 'd007d546-3415-4d63-9aa3-ed1e3b507957'
ORDER BY a.fecaprobacion DESC;

-- Ver el estado actual de la requisición
SELECT 
    'ESTADO ACTUAL DE REQUISICION:' as debug,
    r.codigorequisicion,
    r.idestadosolicitud,
    es.nomestado
FROM requisiciones.requisiciones r
JOIN requisiciones.estado_solicitud es ON r.idestadosolicitud = es.idestadosolicitud
WHERE r.idrequisicion = 'd007d546-3415-4d63-9aa3-ed1e3b507957';
