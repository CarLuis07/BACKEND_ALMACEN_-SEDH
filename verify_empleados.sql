SELECT emailinstitucional, dni, dnijefeinmediato
FROM usuarios.empleados
WHERE emailinstitucional IN (
  'humberto.zelaya@sedh.gob.hn',
  'luis.cardona@sedh.gob.hn',
  'emerson.duron@sedh.gob.hn',
  'admin@test.com',
  'tu.email@dominio.com'
)
ORDER BY emailinstitucional;
