-- Ver estructura de acceso.empleados_roles
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_schema='acceso' 
AND table_name='empleados_roles'
ORDER BY ordinal_position;
