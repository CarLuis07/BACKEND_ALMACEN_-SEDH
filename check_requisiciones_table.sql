-- 1. Estructura de la tabla
\d requisiciones.requisiciones

-- 2. Contar registros
SELECT COUNT(*) as total_registros FROM requisiciones.requisiciones;

-- 3. Listar últimos registros
SELECT idrequisicion, codrequisicion, nomempleado, fecsolicitud, estgeneral 
FROM requisiciones.requisiciones 
ORDER BY creadoen DESC 
LIMIT 10;

-- 4. Ver triggers en la tabla
SELECT trigger_name, event_manipulation, action_statement
FROM information_schema.triggers
WHERE event_object_table = 'requisiciones'
AND event_object_schema = 'requisiciones';

-- 5. Ver constrains
SELECT constraint_name, constraint_type
FROM information_schema.table_constraints
WHERE table_name = 'requisiciones'
AND table_schema = 'requisiciones';

-- 6. Ver índices
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'requisiciones'
AND schemaname = 'requisiciones';
