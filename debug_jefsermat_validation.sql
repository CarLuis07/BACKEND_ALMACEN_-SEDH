-- Verificar si hay validación que bloquee inserts en responder_requisicion_jefe_materiales

-- 1. Ver requisiciones EN ESPERA que fueron actualizadas por usuario JefSerMat
SELECT r.codrequisicion, r.estgeneral, r.actualizadopor, r.actualizadoen,
       COUNT(a.idaprobacion) FILTER (WHERE a.rol = 'JefSerMat') as aprobaciones_jefsermat
FROM requisiciones.requisiciones r
LEFT JOIN requisiciones.aprobaciones a ON a.idrequisicion = r.idrequisicion AND a.rol = 'JefSerMat'
WHERE r.estgeneral = 'EN ESPERA'
  AND r.actualizadoen >= '2026-01-12'
GROUP BY r.codrequisicion, r.estgeneral, r.actualizadopor, r.actualizadoen
ORDER BY r.actualizadoen DESC;

-- 2. Ver todas las aprobaciones de requisiciones EN ESPERA actualizadas hoy
SELECT r.codrequisicion, a.rol, a.estadoaprobacion, a.emailinstitucional, a.fecaprobacion
FROM requisiciones.requisiciones r
LEFT JOIN requisiciones.aprobaciones a ON a.idrequisicion = r.idrequisicion
WHERE r.estgeneral = 'EN ESPERA'
  AND r.actualizadoen >= '2026-01-12'
ORDER BY r.codrequisicion, a.fecaprobacion DESC NULLS LAST;

-- 3. Ver función actual desplegada en el servidor
SELECT pg_get_functiondef(p.oid)
FROM pg_proc p
JOIN pg_namespace n ON n.oid = p.pronamespace
WHERE n.nspname = 'requisiciones'
  AND p.proname = 'responder_requisicion_jefe_materiales'
LIMIT 1;
