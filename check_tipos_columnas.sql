-- Ver la definición de la función existente (si hay backup o versión anterior)
SELECT pg_get_functiondef(oid)
FROM pg_proc
WHERE proname = 'requisiciones_pendientes_jefe_materiales'
AND pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'requisiciones');

-- Ver tipos de las columnas problemáticas
SELECT column_name, data_type, numeric_precision, numeric_scale
FROM information_schema.columns 
WHERE table_schema='requisiciones' 
AND table_name='requisiciones' 
AND column_name IN ('prointermedio', 'profinal', 'fecsolicitud', 'codprograma');
