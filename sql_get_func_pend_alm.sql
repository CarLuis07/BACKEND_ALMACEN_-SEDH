-- Definición de la función requisiciones_pendientes_almacen
SELECT pg_get_functiondef(oid)
FROM pg_proc
WHERE proname = 'requisiciones_pendientes_almacen';
