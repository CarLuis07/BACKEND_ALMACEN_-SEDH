-- Ver aprobaciones actuales de UIT-007-2026
SELECT a.rol, a.estadoaprobacion, a.emailinstitucional, a.fecaprobacion
FROM requisiciones.aprobaciones a
JOIN requisiciones.requisiciones r ON r.idrequisicion=a.idrequisicion
WHERE r.codrequisicion='UIT-007-2026'
ORDER BY a.fecaprobacion DESC NULLS LAST;

-- Ver si aparece en pendientes de almacén
SELECT codrequisicion
FROM requisiciones.requisiciones_pendientes_almacen('maria.hernandez@sedh.gob.hn')
WHERE codrequisicion='UIT-007-2026';
