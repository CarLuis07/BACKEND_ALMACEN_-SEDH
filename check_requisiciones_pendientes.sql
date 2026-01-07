-- Verificar la estructura de la función requisiciones_pendientes_jefe
-- Ejecutar en el servidor de base de datos

-- Ver la definición de la función
SELECT pg_get_functiondef(oid) 
FROM pg_proc 
WHERE proname = 'requisiciones_pendientes_jefe';

-- Ver el tipo de retorno
SELECT 
    p.proname AS nombre_funcion,
    pg_get_function_result(p.oid) AS tipo_retorno
FROM pg_proc p
WHERE p.proname = 'requisiciones_pendientes_jefe';

-- Ejecutar la función con un email de prueba para ver qué devuelve
-- SELECT * FROM requisiciones.requisiciones_pendientes_jefe('email@ejemplo.com');
