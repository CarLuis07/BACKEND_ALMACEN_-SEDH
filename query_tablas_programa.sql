-- Buscar tablas con "programa" en el nombre
SELECT table_schema, table_name 
FROM information_schema.tables 
WHERE table_name LIKE '%programa%' 
ORDER BY table_schema, table_name;

-- Ver columnas relacionadas con programa en la tabla requisiciones
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_schema = 'requisiciones' 
AND table_name = 'requisiciones'
AND column_name LIKE '%programa%'
ORDER BY ordinal_position;
