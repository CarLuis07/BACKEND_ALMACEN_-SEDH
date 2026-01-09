-- Test manual: Aprobar UIT-001-2026 como JefSerMat
-- Usar el email exacto que tiene el rol
SELECT requisiciones.responder_requisicion_jefe_materiales(
    'bbc2fd04-ceac-4db2-b27b-290a0e6c6b7e'::uuid,
    'escarleth.ortiz@sedh.gob.hn'::text,
    'APROBADO'::text,
    'Prueba manual'::text,
    '[{"id_producto": "7c38dbc6-4686-4b46-be0d-abbd40c1a328", "nueva_cantidad": 1.0}]'::text
) AS resultado;

-- Ver si se insertó
SELECT 'Aprobaciones después:' as paso;
SELECT rol, estadoaprobacion, fecaprobacion 
FROM requisiciones.aprobaciones 
WHERE idrequisicion = 'bbc2fd04-ceac-4db2-b27b-290a0e6c6b7e'
ORDER BY fecaprobacion DESC NULLS LAST;
