-- Llamar manualmente a la función para UIT-064-2025
SELECT requisiciones.responder_requisicion_jefe_materiales(
  'd007d546-3415-4d63-9aa3-ed1e3b507957'::uuid,
  'escarleth.ortiz@sedh.gob.hn',
  'APROBADO',
  NULL,
  '[]'::jsonb
) AS resultado;

-- Verificar aprobaciones después
SELECT a.rol, a.estadoaprobacion, a.fecaprobacion, a.emailinstitucional
FROM requisiciones.aprobaciones a
WHERE a.idrequisicion = 'd007d546-3415-4d63-9aa3-ed1e3b507957'
ORDER BY a.fecaprobacion DESC NULLS LAST;
