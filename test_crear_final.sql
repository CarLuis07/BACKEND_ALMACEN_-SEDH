-- Test final con producto que SÍ existe
SELECT requisiciones.crear_requisicion(
    'luis.cardona@sedh.gob.hn',
    1.00,
    2,
    'Test final post-fix 12-ene',
    100.00,
    '[
        {"nombre": "Agua", "cantidad": 2, "gasUnitario": 25.00, "gasTotalProducto": 50.00},
        {"nombre": "Aguazul", "cantidad": 2, "gasUnitario": 25.00, "gasTotalProducto": 50.00}
    ]'::json
) AS nuevo_id_requisicion;

-- Contar registros
SELECT COUNT(*) as total_final FROM requisiciones.requisiciones;

-- Ver última
SELECT codrequisicion, nomempleado, estgeneral, gastotaldelpedido, 
       TO_CHAR(fecha_hora_creacion, 'YYYY-MM-DD HH24:MI:SS') as creada
FROM requisiciones.requisiciones
ORDER BY fecha_hora_creacion DESC
LIMIT 1;

-- Ver detalles de la última
SELECT r.codrequisicion, p.nomproducto, dr.cantsolicitada, dr.gasunitario, dr.gastotalproducto
FROM requisiciones.requisiciones r
JOIN requisiciones.detalle_requisicion dr ON r.idrequisicion = dr.idrequisicion
JOIN productos.productos p ON p.idproducto = dr.idproducto
ORDER BY r.fecha_hora_creacion DESC
LIMIT 5;
