# Interfaz de Almacén - Requisiciones Pendientes e Historial

## Vista para Empleado de Almacén

### Tabs Disponibles:
1. **⏳ Pendientes de Aprobación** (Principal)
   - Muestra requisiciones aprobadas por otras áreas
   - Botones: "Revisar" (para validar cantidades)
   - Botones: "Finalizar" (cuando está aprobada)

2. **📋 Historial** (Nuevo)
   - Muestra requisiciones: Aprobadas, Entregadas, Rechazadas
   - Botones: "📥 Descargar PDF" 
   - Botones: "🖨️ Imprimir"

### Funcionalidades:

#### Descargar PDF
- Genera un PDF en el navegador (cliente-side)
- Incluye información completa de la requisición
- Formato profesional con:
  - Código de requisición
  - Datos del solicitante
  - Lista de productos
  - Total del pedido
  - Fecha de generación
- Se descarga con nombre: `Requisicion_COD_TIMESTAMP.pdf`

#### Imprimir
- Abre el diálogo de impresión del navegador
- Mantiene el formato profesional
- Compatible con cualquier impresora

### Flujo de Trabajo del Empleado de Almacén:

```
1. Entra a la aplicación
   ↓
2. Ve SOLO dos tabs: "Pendientes" e "Historial"
   (No ve "Mis Requisiciones" ni "Nueva Requisición")
   ↓
3. En "Pendientes de Aprobación":
   - Revisa requisiciones aprobadas por Jefe/Gerente
   - Valida cantidades si es necesario
   - Aprueba o rechaza
   - Finaliza la requisición cuando está lista
   ↓
4. En "Historial":
   - Ve todas las requisiciones procesadas
   - Descarga PDFs para archivar
   - Imprime para documentación física
```

### Cambios de Rol

| Rol | Tabs Visibles | Acciones |
|-----|---------------|----------|
| Empleado de Almacén | Pendientes, Historial | Revisar, Finalizar, Descargar PDF, Imprimir |
| Solicitante | Mis Requisiciones, Nueva Req, Pendientes, Historial | Crear, Ver, Seguimiento |
| Jefe | Todas | Aprobar, Todos |
| Gerente | Todas | Aprobar, Todos |

### Generación de PDF

**Método:** Cliente-side (jsPDF)
- ✅ No requiere servidor
- ✅ Rápido
- ✅ Funciona sin conexión (una vez cargado)
- ✅ Fácil de imprimir

**Contenido del PDF:**
- Código de requisición
- Información del solicitante
- Dependencia
- Estado
- Lista de productos (cantidad, precio unitario, subtotal)
- Total del pedido
- Fecha y hora de generación

### Implementación Técnica

**Función Principal:** `generarPDFRequisicion(req, descargar)`
- `req`: Objeto de la requisición
- `descargar`: `true` para descargar, `false` para imprimir

**Dependencia:** jsPDF (librería externa)
```html
<!-- Ya incluida en reportes-completo.html, disponible globalmente -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
```

### Testing

Para probar como empleado de almacén:
1. Loguearse con usuario que tenga rol "empleado de almacen" o similar
2. Ver que solo hay dos tabs
3. Hacer clic en "Historial"
4. Seleccionar una requisición aprobada
5. Cliquear "Descargar PDF" para descargar
6. Cliquear "Imprimir" para imprimir

## Cambios Recientes

✅ Agregado tab "Historial" con ID `tabHistorial`
✅ Nueva función `cargarHistorialRequisiciones()`
✅ Nueva función `renderizarHistorialRequisiciones()`
✅ Nueva función `generarPDFRequisicion(req, descargar)`
✅ Botones de descarga e impresión
✅ Configuración de visibilidad de tabs por rol actualizada
