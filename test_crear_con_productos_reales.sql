-- Ver nombres de productos disponibles
SELECT nomproducto, canstock 
FROM productos.productos 
WHERE canstock > 0
ORDER BY nomproducto
LIMIT 20;

-- Test con producto real
SELECT requisiciones.crear_requisicion(
    'luis.cardona@sedh.gob.hn',
    1.00,
    2,
    'Test post-fix con producto válido',
    45.00,
    '[
        {"nombre": "LAPICERO AZUL", "cantidad": 2, "gasUnitario": 15.00, "gasTotalProducto": 30.00},
        {"nombre": "LAPICERO NEGRO", "cantidad": 1, "gasUnitario": 15.00, "gasTotalProducto": 15.00}
    ]'::json
) AS nuevo_id;

-- Verificar inserción
SELECT COUNT(*) as total_final FROM requisiciones.requisiciones;

-- Ver última requisición
SELECT codrequisicion, nomempleado, estgeneral, gastotaldelpedido, fecha_hora_creacion
FROM requisiciones.requisiciones
ORDER BY fecha_hora_creacion DESC
LIMIT 3;
