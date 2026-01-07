-- Solo modificar la condición WHERE para agregar el filtro NOT EXISTS
-- Mantener TODO lo demás igual que la función original

-- Primero verificar cuántas requisiciones devuelve actualmente
SELECT COUNT(*) as total_sin_filtro
FROM requisiciones.requisiciones_pendientes_jefe_materiales('escarleth.nunez@sedh.gob.hn');

-- Luego insertar registro de test en aprobaciones para JefSerMat si no existe
-- (simulando que ya aprobó UIT-001-2026)
DO $$
BEGIN
    -- Solo insertar si no existe
    IF NOT EXISTS (
        SELECT 1 FROM requisiciones.aprobaciones a
        JOIN requisiciones.requisiciones r ON r.idrequisicion = a.idrequisicion
        WHERE r.codrequisicion = 'UIT-001-2026' AND a.rol = 'JefSerMat'
    ) THEN
        INSERT INTO requisiciones.aprobaciones (
            idaprobacion, 
            idrequisicion, 
            emailinstitucional, 
            rol, 
            estadoaprobacion, 
            comentario, 
            fecaprobacion
        )
        SELECT 
            uuid_generate_v4(),
            r.idrequisicion,
            'escarleth.nunez@sedh.gob.hn',
            'JefSerMat',
            'APROBADO',
            'Test aprobación',
            CURRENT_TIMESTAMP
        FROM requisiciones.requisiciones r
        WHERE r.codrequisicion = 'UIT-001-2026';
    END IF;
END $$;

-- Ahora verificar que la función original YA filtra correctamente
-- (si tiene lógica interna de filtrado)
SELECT COUNT(*) as total_con_filtro_interno
FROM requisiciones.requisiciones_pendientes_jefe_materiales('escarleth.nunez@sedh.gob.hn');

-- Ver cuáles devuelve
SELECT codrequisicion 
FROM requisiciones.requisiciones_pendientes_jefe_materiales('escarleth.nunez@sedh.gob.hn')
ORDER BY fecsolicitud DESC;
