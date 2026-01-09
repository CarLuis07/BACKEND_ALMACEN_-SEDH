SELECT pg_get_functiondef(oid) 
FROM pg_proc 
WHERE proname = 'responder_requisicion_jefe_materiales' 
AND pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'requisiciones')
ORDER BY oid DESC
LIMIT 1;
