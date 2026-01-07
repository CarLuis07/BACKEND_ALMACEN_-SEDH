-- Actualizar función para que NO devuelva requisiciones ya aprobadas/rechazadas por JefSerMat
DROP FUNCTION IF EXISTS requisiciones.requisiciones_pendientes_jefe_materiales(TEXT);

CREATE OR REPLACE FUNCTION requisiciones.requisiciones_pendientes_jefe_materiales(p_email TEXT)
RETURNS TABLE (
    idrequisicion UUID,
    codrequisicion VARCHAR(50),
    nombreempleado VARCHAR(100),
    dependencia TEXT,
    fecsolicitud DATE,
    codprograma INTEGER,
    prointermedio NUMERIC(10,2),
    profinal INTEGER,
    obsempleado TEXT,
    gastotaldelpedido NUMERIC(14,2),
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
        COALESCE(p.codigo, 0)::INTEGER as codprograma,
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
    LEFT JOIN programas.programas p ON p.idprograma = r.codprograma
    WHERE r.estgeneral IN ('PENDIENTE', 'PENDIENTE JEFE MATERIALES', 'ESPERA JEFE MATERIALES')
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
