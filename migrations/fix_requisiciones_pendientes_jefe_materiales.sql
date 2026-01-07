-- Fix: Corregir referencia de tabla programas.programas → requisiciones.programas
-- y añadir filtro para excluir requisiciones ya aprobadas/rechazadas por JefSerMat

DROP FUNCTION IF EXISTS requisiciones.requisiciones_pendientes_jefe_materiales(TEXT) CASCADE;

CREATE OR REPLACE FUNCTION requisiciones.requisiciones_pendientes_jefe_materiales(p_email TEXT)
RETURNS TABLE(
    idrequisicion UUID,
    codrequisicion VARCHAR,
    nombreempleado VARCHAR,
    dependencia VARCHAR,
    fecsolicitud DATE,  -- Cambiado de TIMESTAMP a DATE
    codprograma INTEGER,
    prointermedio NUMERIC(10,2),  -- Cambiado de INTEGER a NUMERIC(10,2)
    profinal INTEGER,
    obsempleado TEXT,
    gastotaldelpedido NUMERIC,
    productos JSON
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        r.idrequisicion,
        r.codrequisicion,
        r.nomempleado as nombreempleado,
        d.nomdependencia as dependencia,
        r.fecsolicitud,
        CASE 
            WHEN p.codigo ~ '^\d+$' THEN p.codigo::INTEGER 
            ELSE 0 
        END as codprograma,  -- Convertir VARCHAR a INTEGER solo si es numérico
        r.prointermedio,
        r.profinal,
        r.obsempleado,
        r.gastotaldelpedido,
        (
            SELECT json_agg(json_build_object(
                'idProducto', dr.idproducto,
                'nombre', prod.nomproducto,
                'cantidad', dr.cantsolicitada,
                'gasUnitario', dr.gasunitario,
                'gasTotalProducto', dr.gastotalproducto
            ))
            FROM requisiciones.detalle_requisicion dr
            JOIN productos.productos prod ON prod.idproducto = dr.idproducto
            WHERE dr.idrequisicion = r.idrequisicion
        ) as productos
    FROM requisiciones.requisiciones r
    JOIN usuarios.dependencias d ON d.iddependencia = r.iddependencia
    LEFT JOIN requisiciones.programas p ON p.idprograma = r.codprograma  -- CORREGIDO: requisiciones.programas
    WHERE r.estgeneral IN ('PENDIENTE', 'PENDIENTE JEFE MATERIALES', 'ESPERA JEFE MATERIALES', 'EN ESPERA')  -- Agregado 'EN ESPERA'
    -- FILTRO CLAVE: Excluir las que ya tienen aprobación/rechazo de JefSerMat
    AND NOT EXISTS (
        SELECT 1
        FROM requisiciones.aprobaciones a
        WHERE a.idrequisicion = r.idrequisicion
        AND a.rol = 'JefSerMat'
        AND a.estadoaprobacion IN ('APROBADO', 'RECHAZADO')
    )
    ORDER BY r.fecsolicitud DESC;
END;
$$ LANGUAGE plpgsql;
