-- 1) Requisición por código
WITH r AS (
  SELECT * FROM requisiciones.requisiciones WHERE codrequisicion = 'UIT-007-2026'
)
SELECT r.idrequisicion, r.codrequisicion, r.estgeneral, r.gastotaldelpedido,
       r.creadoen, r.creadopor, r.actualizadoen, r.actualizadopor
FROM r;

-- 2) Aprobaciones por rol/estado
SELECT a.idrequisicion, r.codrequisicion, a.emailinstitucional, a.rol, a.estadoaprobacion, a.fecaprobacion
FROM requisiciones.aprobaciones a
JOIN requisiciones.requisiciones r ON r.idrequisicion = a.idrequisicion
WHERE r.codrequisicion = 'UIT-007-2026'
ORDER BY a.fecaprobacion DESC NULLS LAST;

-- 3) ¿Aparece en pendientes de almacén?
SELECT codrequisicion
FROM requisiciones.requisiciones_pendientes_almacen('maria.hernandez@sedh.gob.hn')
WHERE codrequisicion = 'UIT-007-2026';

-- 4) Estado actual de todos los pendientes de almacén (muestra top 15)
SELECT codrequisicion, estgeneral
FROM requisiciones.requisiciones r
WHERE r.idrequisicion IN (
  SELECT t.idrequisicion
  FROM requisiciones.requisiciones_pendientes_almacen('maria.hernandez@sedh.gob.hn') t
)
ORDER BY r.fecsolicitud DESC
LIMIT 15;

-- 5) Ver definiciones resumidas de funciones relevantes
SELECT proname, pg_get_functiondef(p.oid) AS def
FROM pg_proc p
JOIN pg_namespace n ON n.oid = p.pronamespace
WHERE n.nspname = 'requisiciones'
  AND proname IN ('requisiciones_pendientes_almacen','responder_requisicion_jefe_materiales')
ORDER BY proname;