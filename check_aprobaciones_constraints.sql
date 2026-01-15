-- Ver constraints y triggers en la tabla aprobaciones
\d requisiciones.aprobaciones

-- Ver si hay índices únicos que bloqueen
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE schemaname = 'requisiciones' 
  AND tablename = 'aprobaciones';

-- Ver triggers
SELECT trigger_name, event_manipulation, action_statement
FROM information_schema.triggers
WHERE event_object_schema = 'requisiciones'
  AND event_object_table = 'aprobaciones';
