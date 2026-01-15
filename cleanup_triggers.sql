-- 1. Eliminar trigger duplicado
DROP TRIGGER IF EXISTS trigger_generar_codigo_requisicion ON requisiciones.requisiciones;

-- 2. Verificar que solo quede tr_generar_codigo_requisicion
SELECT trigger_name 
FROM information_schema.triggers
WHERE event_object_table = 'requisiciones'
AND event_object_schema = 'requisiciones';
