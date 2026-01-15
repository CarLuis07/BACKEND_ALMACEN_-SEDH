# Formato PDF Oficial SEDH - Requisiciones

## Cambio Realizado

El PDF generado ahora sigue el **formato oficial SEDH** para "REQUISICIÓN DE BIENES DE CONSUMO", basado en el documento físico usado en Honduras.

## Estructura del PDF

```
┌──────────────────────────────────────────────────────────┐
│         REQUISICIÓN DE BIENES DE CONSUMO                 │
│         HONDURAS - SEDH                                  │
├──────────────────────────────────────────────────────────┤
│                                            No. UIT-064-2025
│                                                           │
│ Fecha solicitud:           05/01/2026                    │
│ Nombre solicitante:        Humberto Josue Zelaya        │
│ Unidad ó Dependencia:      UNIDAD DE INFOTECNOLOGÍA     │
│ Programa Intermedio:       11                            │
│                                                           │
├─────────┬──────────────────────────┬──────────┬──────────┤
│Cantidad │ Artículo                 │ Objeto   │ Entregad │
│         │                          │ del gasto│ o        │
├─────────┼──────────────────────────┼──────────┼──────────┤
│   1.0   │ PEPSI                    │ L.45.00  │          │
├─────────┼──────────────────────────┼──────────┼──────────┤
│         │                          │          │          │
├─────────┼──────────────────────────┼──────────┼──────────┤
│ (15 filas para llenar)                                   │
│                                                           │
│                            TOTAL: L. 45.00              │
│                                                           │
├──────────────────────────────────────────────────────────┤
│ Autorización Subgerencia de Recursos Materiales          │
│ _______________________ (firma/sello)                    │
│                                                           │
│ Observaciones:                                           │
│ ┌────────────────────────────────────────────────────┐  │
│ │ (Espacio en blanco para llenar a mano)             │  │
│ └────────────────────────────────────────────────────┘  │
│                                                           │
│ Entregado por: _____________  Recibido por: _________   │
│                                                           │
│ Fecha y hora: 15/01/2026                                 │
├──────────────────────────────────────────────────────────┤
│ Generado por Sistema de Almacén SEDH - 19:45:32         │
└──────────────────────────────────────────────────────────┘
```

## Campos Automáticos (Del Sistema)

✅ **Número de Requisición:** UIT-064-2025 (del código)
✅ **Fecha de Solicitud:** 05/01/2026 (del sistema)
✅ **Nombre del Solicitante:** Humberto Josue Zelaya (del sistema)
✅ **Unidad o Dependencia:** UNIDAD DE INFOTECNOLOGÍA (del sistema)
✅ **Programa Intermedio:** 11 (del sistema)
✅ **Cantidad:** Cantidad solicitada (del sistema)
✅ **Artículo:** Nombre del producto (del sistema)
✅ **Objeto del Gasto:** Total del producto (del sistema)
✅ **Fecha y Hora:** Actual (del sistema)

## Campos Manuales (Para Llenar con Firma/Sello)

❌ **Autorización Subgerencia:** Línea vacía para firma/sello
❌ **Observaciones:** Espacio en blanco para comentarios
❌ **Entregado por:** Línea para firma
❌ **Recibido por:** Línea para firma
❌ **Entregado:** Columna vacía en tabla (para completar manualmente)

## Características

### Tabla de Productos
- **Cantidad:** Desde el sistema
- **Artículo:** Desde el sistema
- **Objeto del gasto:** Costo total desde el sistema
- **Entregado:** Vacío para completar (sí/no/cantidad entregada)
- **15 filas:** Permite hasta 15 artículos por página

### Formato
- **Tamaño:** Carta (Letter: 8.5" x 11")
- **Orientación:** Vertical (Portrait)
- **Márgenes:** 1 cm
- **Tipografía:** Helvetica (compatible universal)
- **Colores:** Blanco y negro (apto para fotocopias)

### Para Imprimir
- ✅ Compatible con cualquier impresora
- ✅ Se ve bien en blanco y negro
- ✅ Pueden agregar firmas digitales antes de imprimir
- ✅ Se puede escanear y archivar

## Funciones Disponibles

### Descargar PDF
```javascript
descargarPDFRequisicion(requisicion)
// Descarga archivo: Requisicion_UIT-064-2025_1234567890.pdf
```

### Imprimir
```javascript
imprimirRequisicion(requisicion)
// Abre diálogo de impresión del navegador
```

## Cambios desde Versión Anterior

| Aspecto | Antes | Ahora |
|---------|-------|-------|
| Encabezado | "REQUISICIÓN DE PEDIDO" | "REQUISICIÓN DE BIENES DE CONSUMO" |
| Estructura | Simple lista | Tabla profesional SEDH |
| Campos | No estándar | Orden oficial SEDH |
| Firmas | Nada | Espacios para firma/sello |
| Observaciones | Ninguna | Espacio dedicado |
| Entrega | No seguimiento | Columna "Entregado" |
| Total | Al final | Bien visible |

## Testing

1. Ir a http://192.168.180.164:8081/requisiciones
2. Cambiar a tab "Historial" (empleado de almacén)
3. Seleccionar una requisición aprobada
4. Cliquear "📥 Descargar PDF"
5. Abrir PDF generado
6. Verificar que tiene:
   - ✓ Número de requisición correcto
   - ✓ Fecha del sistema
   - ✓ Nombre del solicitante
   - ✓ Dependencia
   - ✓ Programa intermedio
   - ✓ Productos en tabla
   - ✓ Total correcto
   - ✓ Espacios para firmas

## Implementación

**Función:** `generarPDFRequisicion(req, descargar)`
**Ubicación:** `app/frontend/requisiciones.html` línea ~1813
**Librería:** jsPDF 2.5.1
**Formato de Salida:** PDF

## Próximos Pasos Opcionales

- [ ] Agregar logo SEDH como imagen
- [ ] Agregar código QR con número de requisición
- [ ] Multi-página automática si hay >15 productos
- [ ] Numeración de páginas (Página 1 de X)
