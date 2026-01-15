SELECT pg_get_functiondef(oid)
FROM pg_proc
WHERE proname = 'responder_requisicion_jefe_materiales';
