-- Eliminar aprobación de JefSerMat para UIT-001-2026
DELETE FROM requisiciones.aprobaciones
WHERE idrequisicion = (SELECT idrequisicion FROM requisiciones.requisiciones WHERE codrequisicion = 'UIT-001-2026')
AND rol = 'JefSerMat';

-- Verificar estado final
SELECT 'Aprobaciones finales de UIT-001-2026:' as paso;
SELECT 
    r.codrequisicion,
    a.rol,
    a.estadoaprobacion,
    a.fecaprobacion
FROM requisiciones.aprobaciones a
JOIN requisiciones.requisiciones r ON r.idrequisicion = a.idrequisicion
WHERE r.codrequisicion = 'UIT-001-2026'
ORDER BY a.fecaprobacion;

-- Verificar cuántas requisiciones ve JefSerMat
SELECT 'Total requisiciones pendientes para JefSerMat:' as paso;
SELECT COUNT(*) as total
FROM requisiciones.requisiciones_pendientes_jefe_materiales('escarleth.nunez@sedh.gob.hn');

-- Verificar que UIT-001-2026 esté en la lista
SELECT 'UIT-001-2026 está en la lista?' as paso;
SELECT codrequisicion
FROM requisiciones.requisiciones_pendientes_jefe_materiales('escarleth.nunez@sedh.gob.hn')
WHERE codrequisicion = 'UIT-001-2026';
