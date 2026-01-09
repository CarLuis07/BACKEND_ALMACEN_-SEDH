-- Debug: Ver qué emails hay en la base de datos para JefSerMat
SELECT 
    'EMPLEADOS CON ROLE JEFSERMAT:' as debug,
    e.emailinstitucional,
    e.nombre,
    er.idrol,
    r.nomrol,
    er.actlaboralmente
FROM usuarios.empleados e
JOIN acceso.empleados_roles er ON e.idemp = er.idemp
JOIN acceso.roles r ON er.idrol = r.idrol
WHERE r.nomrol = 'JefSerMat'
  AND er.actlaboralmente = true
ORDER BY e.emailinstitucional;

-- Ver últimas llamadas a la función (si tenemos logs)
SELECT 
    'ULTIMAS APROBACIONES:' as debug,
    idrequisicion,
    rol,
    estadoaprobacion,
    fecaprobacion
FROM requisiciones.aprobaciones
WHERE rol = 'JefSerMat'
ORDER BY fecaprobacion DESC
LIMIT 10;
