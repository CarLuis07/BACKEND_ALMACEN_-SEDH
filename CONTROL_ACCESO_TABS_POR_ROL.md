# Control de Acceso a Tabs según Rol

## Cambios Realizados

### 1. **Identificación de Tabs con IDs**
Se agregaron IDs a los botones de navegación en [app/frontend/requisiciones.html](app/frontend/requisiciones.html#L601):
```html
<button class="nav-tab active" id="tabMisRequisiciones" onclick="showTab('mis-requisiciones')">
<button class="nav-tab" id="tabNuevaRequisicion" onclick="showTab('nueva-requisicion')">
<button class="nav-tab" id="tabPendientes" onclick="showTab('pendientes-aprobacion')">
```

### 2. **Nueva Función: `configurarTabsPorRol()`**
Función que analiza el rol del usuario desde el JWT y configura la visibilidad de tabs:

```javascript
function configurarTabsPorRol() {
    const token = localStorage.getItem('token');
    const payload = parseJwt(token);
    const roles = normalizarRoles(payload);
    
    const esEmpleadoAlmacen = roles.some(r => 
        ['empleado de almacen', 'empleado de almac', 'almacen', 'almac', 'empalmacen']
        .some(alias => r === alias || r.includes(alias))
    );

    if (esEmpleadoAlmacen) {
        // Ocultar tabs de solicitante
        document.getElementById('tabMisRequisiciones').style.display = 'none';
        document.getElementById('tabNuevaRequisicion').style.display = 'none';
        document.getElementById('mis-requisiciones').style.display = 'none';
        document.getElementById('nueva-requisicion').style.display = 'none';
        
        // Mostrar solo requisiciones pendientes
        showTab('pendientes-aprobacion');
    }
}
```

## Flujo de Acceso por Rol

### Empleado de Almacén (EmpAlmacen)
| Acción | Permitido | Razón |
|--------|-----------|-------|
| Ver requisiciones pendientes aprobadas | ✅ Sí | Necesita procesarlas |
| Crear nueva requisición | ❌ No | No es su responsabilidad |
| Ver "Mis Requisiciones" | ❌ No | Solo ve las que debe procesar |
| Generar PDF | ❌ No | Solo al finalizar (no es su responsabilidad crear PDFs) |
| Aprobar/Rechazar | ✅ Sí | Valida y aprueba cantidades |
| Finalizar requisición | ✅ Sí | Marca como entregada, notifica solicitante |

### Otros Roles (Solicitantes, Jefes, Gerentes, etc.)
- ✅ Ver "Mis Requisiciones"
- ✅ Crear "Nueva Requisición"
- ✅ Ver "Pendientes de Aprobación"

## Inicialización
La función se ejecuta en `DOMContentLoaded`:
```javascript
document.addEventListener('DOMContentLoaded', () => {
    configurarTabsPorRol();  // ← Configurar visibilidad PRIMERO
    cargarMisRequisiciones();
    cargarProgramasIntermedio();
    renderResumenCarrito();
});
```

## Deployment

✅ **Cambio Local:** `app/frontend/requisiciones.html`
✅ **Publicado en GitHub:** Commit 33da66a
✅ **Actualizado en Servidor:** `/opt/almacen-backend/app/frontend/requisiciones.html`

## Beneficios

1. **Mejor UX para Empleado de Almacén**
   - Interfaz simplificada
   - Solo ve lo que necesita hacer
   - Menos distracciones

2. **Seguridad**
   - No puede acceder a funciones de solicitante
   - Control basado en roles

3. **Flujo Claro**
   - Empleado recibe requisiciones aprobadas
   - Las procesa (aprueba/rechaza cantidades)
   - Las finaliza cuando están completas

## Notas Importantes

- **No genera PDFs**: El empleado de almacén NO genera PDFs en su interfaz. El PDF se genera automáticamente cuando **finaliza** la requisición (acción que debe hacer).
- **Sin acceso a crear requisiciones**: El tab "Nueva Requisición" está completamente oculto para este rol.
- **Sin edición de programas**: El empleado solo trabaja con requisiciones previamente configuradas.
