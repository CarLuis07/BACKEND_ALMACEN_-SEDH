-- 1) Aprobaciones para UIT-064-2025
SELECT a.rol, a.estadoaprobacion, a.fecaprobacion, a.emailinstitucional
FROM requisiciones.aprobaciones a
WHERE a.idrequisicion = 'd007d546-3415-4d63-9aa3-ed1e3b507957'
ORDER BY a.fecaprobacion DESC NULLS LAST;

-- 2) Estado general de la requisición
SELECT codrequisicion, estgeneral, actualizadoen, actualizadopor
FROM requisiciones.requisiciones
WHERE idrequisicion = 'd007d546-3415-4d63-9aa3-ed1e3b507957';

-- 3) Pendientes para EmpAlmacen
SELECT * FROM requisiciones.requisiciones_pendientes_almacen('maria.hernandez@sedh.gob.hn') LIMIT 20;
