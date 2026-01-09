-- Ver estado de UIT-001-2026
SELECT 
    codrequisicion,
    estgeneral,
    nomempleado,
    fecsolicitud,
    creadopor
FROM requisiciones.requisiciones
WHERE codrequisicion = 'UIT-001-2026';

-- Ver todas sus aprobaciones
SELECT 
    rol,
    estadoaprobacion,
    fecaprobacion
FROM requisiciones.aprobaciones
WHERE idrequisicion = (SELECT idrequisicion FROM requisiciones.requisiciones WHERE codrequisicion = 'UIT-001-2026')
ORDER BY fecaprobacion DESC;
