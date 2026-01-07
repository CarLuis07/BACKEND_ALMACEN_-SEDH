-- Ver estructura de la tabla aprobaciones
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_schema = 'requisiciones' 
AND table_name = 'aprobaciones'
ORDER BY ordinal_position;

-- Ver estructura de la tabla programas
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_schema = 'requisiciones' 
AND table_name = 'programas'
ORDER BY ordinal_position;
