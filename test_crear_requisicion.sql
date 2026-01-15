-- TEST: Insertar requisición de prueba
SELECT requisiciones.crear_requisicion(
    'luis.cardona@sedh.gob.hn',
    1.00,
    2,
    'Test post-fix 12-ene-2026',
    165.00,
    '[
        {"nombre": "BOTELLA DE AGUA", "cantidad": 5, "gasUnitario": 15.00, "gasTotalProducto": 75.00},
        {"nombre": "LAPICERO AZUL", "cantidad": 6, "gasUnitario": 15.00, "gasTotalProducto": 90.00}
    ]'::json
) AS nuevo_id;

-- Verificar inserción
SELECT COUNT(*) as total_despues FROM requisiciones.requisiciones;

-- Ver última requisición creada
SELECT idrequisicion, codrequisicion, nomempleado, estgeneral, gastotaldelpedido
FROM requisiciones.requisiciones
ORDER BY creadoen DESC, fecha_hora_creacion DESC
LIMIT 5;
