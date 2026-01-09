-- Ver definición de la función responder_requisicion_jefe_materiales
SELECT proname, pronargs, proargtypes::regtype[]
FROM pg_proc
WHERE proname = 'responder_requisicion_jefe_materiales'
AND pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'requisiciones');

-- Ver si existe
SELECT count(*)
FROM pg_proc
WHERE pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'requisiciones')
AND proname LIKE '%responder%';
