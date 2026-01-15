-- Ejecutar manualmente la función con los mismos parámetros del log
-- UUID: c02e1ade-bfae-4161-843a-7c8684b4bc35
-- Producto: b5493226-4c7b-49ca-bdbe-8755d807667e, cantidad: 1.0

\echo '=== ANTES de ejecutar función manualmente ==='
SELECT 
    r.codrequisicion,
    COUNT(a.*) FILTER (WHERE a.rol = 'JefSerMat') as aprobaciones_jefsermat
FROM requisiciones.requisiciones r
LEFT JOIN requisiciones.aprobaciones a ON r.idrequisicion = a.idrequisicion
WHERE r.codrequisicion = 'UIT-004-2026'
GROUP BY r.codrequisicion;

\echo ''
\echo '=== Ejecutando función SQL directamente ==='
SELECT requisiciones.responder_requisicion_jefe_materiales(
    'c02e1ade-bfae-4161-843a-7c8684b4bc35'::UUID,
    'escarleth.ortiz@sedh.gob.hn',
    'APROBADO',
    NULL,
    '[{"id_producto": "b5493226-4c7b-49ca-bdbe-8755d807667e", "nueva_cantidad": 1.0}]'::jsonb
) AS mensaje;

\echo ''
\echo '=== DESPUÉS de ejecutar función ==='
SELECT 
    r.codrequisicion,
    a.rol,
    a.estadoaprobacion,
    a.emailinstitucional,
    a.fecaprobacion
FROM requisiciones.requisiciones r
LEFT JOIN requisiciones.aprobaciones a ON r.idrequisicion = a.idrequisicion
WHERE r.codrequisicion = 'UIT-004-2026'
ORDER BY a.rol;

\echo ''
\echo '=== ¿Ahora aparece para EmpAlmacen? ==='
SELECT COUNT(*) as aparece
FROM requisiciones.requisiciones_pendientes_almacen('almacen@sedh.gob.hn')
WHERE codrequisicion = 'UIT-004-2026';
