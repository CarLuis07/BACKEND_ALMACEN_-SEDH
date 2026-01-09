-- Fix: Corregir función requisiciones_pendientes_almacen
-- Problema: Excluye TODAS las requisiciones con rol EmpAlmacen, incluso las "Pendiente"
-- Solución: Solo excluir las que ya fueron APROBADAS o RECHAZADAS

DROP FUNCTION IF EXISTS requisiciones.requisiciones_pendientes_almacen(TEXT) CASCADE;

CREATE OR REPLACE FUNCTION requisiciones.requisiciones_pendientes_almacen(p_email_almacen TEXT)
RETURNS TABLE(
    idrequisicion UUID,
    codrequisicion VARCHAR,
    nombreempleado VARCHAR,
    dependencia VARCHAR,
    fecsolicitud DATE,
    codprograma INTEGER,
    prointermedio NUMERIC,
    profinal INTEGER,
    obsempleado TEXT,
    gastotaldelpedido NUMERIC,
    productos JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT DISTINCT 
        r.idrequisicion,
        r.codrequisicion,
        r.nomempleado,
        d.nomdependencia,
        r.fecsolicitud,
        r.codprograma,
        r.prointermedio,
        r.profinal,
        r.obsempleado,
        r.gastotaldelpedido,
        (
            SELECT jsonb_agg(jsonb_build_object(
                'idProducto', dr.idproducto,
                'nombre', p.nomproducto,
                'cantidad', dr.cantsolicitada,
                'gasUnitario', dr.gasunitario,
                'gasTotalProducto', dr.gastotalproducto
            ))
            FROM requisiciones.detalle_requisicion dr
            LEFT JOIN productos.productos p ON dr.idproducto = p.idproducto
            WHERE dr.idrequisicion = r.idrequisicion
        ) AS Productos
    FROM requisiciones.requisiciones r
    LEFT JOIN usuarios.dependencias d ON r.iddependencia = d.iddependencia
    WHERE r.estgeneral = 'EN ESPERA'
      -- Debe tener aprobación de JefSerMat
      AND EXISTS (
          SELECT 1 FROM requisiciones.aprobaciones am 
          WHERE am.idrequisicion = r.idrequisicion 
          AND am.rol = 'JefSerMat' 
          AND am.estadoaprobacion = 'APROBADO'
      )
      -- FILTRO CORREGIDO: Excluir solo las que YA fueron procesadas por EmpAlmacen
      AND NOT EXISTS (
          SELECT 1 FROM requisiciones.aprobaciones aa 
          WHERE aa.idrequisicion = r.idrequisicion 
          AND aa.rol = 'EmpAlmacen'
          AND aa.estadoaprobacion IN ('APROBADO', 'RECHAZADO')  -- Solo excluir las procesadas
      )
    ORDER BY r.fecsolicitud ASC;
END;
$$ LANGUAGE plpgsql;
