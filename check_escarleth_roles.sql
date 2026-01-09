-- Ver roles del usuario escarleth
SELECT 
    e.emailinstitucional,
    e.nombre,
    r.nomrol,
    er.actlaboralmente
FROM usuarios.empleados e
JOIN acceso.empleados_roles er ON er.emailinstitucional = e.emailinstitucional
JOIN acceso.roles r ON r.idrol = er.idrol
WHERE e.emailinstitucional LIKE '%escarleth%'
ORDER BY e.emailinstitucional, r.nomrol;
