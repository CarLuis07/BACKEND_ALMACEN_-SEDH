-- Cambiar estado de UIT-001-2026 a EN ESPERA para que sea visible en pendientes
UPDATE requisiciones.requisiciones
SET estgeneral = 'EN ESPERA'
WHERE codrequisicion = 'UIT-001-2026';

-- Eliminar aprobación de JefSerMat si existe
DELETE FROM requisiciones.aprobaciones
WHERE idrequisicion = (SELECT idrequisicion FROM requisiciones.requisiciones WHERE codrequisicion = 'UIT-001-2026')
AND rol = 'JefSerMat';

-- Verificar
SELECT '=== Verificación ===' as paso;
SELECT estgeneral, codrequisicion FROM requisiciones.requisiciones WHERE codrequisicion = 'UIT-001-2026';

-- Ver si ahora está en lista
SELECT 'En lista de JefSerMat?' as paso;
SELECT codrequisicion FROM requisiciones.requisiciones_pendientes_jefe_materiales('escarleth.nunez@sedh.gob.hn')
WHERE codrequisicion = 'UIT-001-2026';
