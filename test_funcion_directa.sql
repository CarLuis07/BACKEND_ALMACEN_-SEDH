-- Simular exactamente lo que hace Python
-- Basado en los logs: [JefSerMat] PARAMS: {'p_id_requisicion': UUID('348aa90b-ed7d-482c-a8eb-a7a8c5cc7c32'), ...}

\echo '=== ANTES de ejecutar función ==='
SELECT 
    r.codrequisicion,
    r.estgeneral,
    COUNT(a.*) as total_aprobaciones
FROM requisiciones.requisiciones r
LEFT JOIN requisiciones.aprobaciones a ON r.idrequisicion = a.idrequisicion
WHERE r.idrequisicion = '348aa90b-ed7d-482c-a8eb-a7a8c5cc7c32'
GROUP BY r.codrequisicion, r.estgeneral;

\echo ''
\echo '=== Ejecutando función con los mismos parámetros que Python ==='
SELECT requisiciones.responder_requisicion_jefe_materiales(
    '348aa90b-ed7d-482c-a8eb-a7a8c5cc7c32'::UUID,
    'escarleth.ortiz@sedh.gob.hn',
    'APROBADO',
    NULL,
    '[{"id_producto": "b5493226-4c7b-49ca-bdbe-8755d807667e", "nueva_cantidad": 2.0}, {"id_producto": "c0d0664f-7929-4504-9bfd-f310ff80aa44", "nueva_cantidad": 2.0}]'::jsonb
) AS mensaje;

\echo ''
\echo '=== DESPUÉS de ejecutar función ==='
SELECT 
    r.codrequisicion,
    r.estgeneral,
    a.rol,
    a.estadoaprobacion,
    a.emailinstitucional
FROM requisiciones.requisiciones r
LEFT JOIN requisiciones.aprobaciones a ON r.idrequisicion = a.idrequisicion
WHERE r.idrequisicion = '348aa90b-ed7d-482c-a8eb-a7a8c5cc7c32'
ORDER BY a.rol;
