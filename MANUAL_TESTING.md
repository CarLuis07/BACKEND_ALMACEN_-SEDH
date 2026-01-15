# MANUAL DE TESTING - FINALIZACION DE REQUISICIONES

## PASO A PASO PARA VERIFICAR LA FUNCIONALIDAD

### Prerequisitos
- ✓ Acceso a http://192.168.180.164:8081
- ✓ Navegador (Chrome, Firefox, Edge, Safari)
- ✓ Crear una requisicion (si no tiene alguna para testing)
- ✓ Tener acceso a account de EmpAlmacen

---

## TESTING BASICO - 5 MINUTOS

### Paso 1: Acceder al Dashboard
```
1. Abrir navegador
2. Ir a: http://192.168.180.164:8081
3. Login con cualquier usuario (ej: empleado1)
4. Click en "REQUISICIONES" o "Mis Requisiciones"
```

### Paso 2: Crear una Requisicion (si es necesario)
```
1. Click en "NUEVA REQUISICION"
2. Seleccionar dependencia
3. Agregar productos:
   - Producto 1: Cantidad 5, Precio $100
   - Producto 2: Cantidad 10, Precio $50
4. Click en "ENVIAR"
5. Anotar el codigo generado (ej: REQ-001)
```

### Paso 3: Aprobar la Requisicion
```
1. Logout del usuario anterior
2. Login como: jefe_inmediato
3. Ir a "REQUISICIONES" 
4. Buscar la requisicion REQ-001 (estado PENDIENTE)
5. Click en "📋 REVISAR"
6. Revisar detalles
7. Click en "APROBAR"
8. Ingresar comentario (opcional)
9. Click en "CONFIRMAR"
```

### Paso 4: Segunda Aprobacion
```
1. Logout
2. Login como: ger_administrativo
3. Ir a "REQUISICIONES"
4. Buscar REQ-001 (estado EN REVISION)
5. Click en "📋 REVISAR"
6. Click en "APROBAR"
7. Confirmar
```

### Paso 5: Tercera Aprobacion
```
1. Logout
2. Login como: jef_servicios_materiales
3. Ir a "REQUISICIONES"
4. Buscar REQ-001 (estado EN REVISION 2)
5. Click en "📋 REVISAR"
6. Click en "APROBAR"
7. Confirmar
```

### Paso 6: FINALIZACION (La nueva funcionalidad!)
```
1. Logout
2. Login como: emp_almacen
3. Ir a "REQUISICIONES"
4. Buscar REQ-001 (ahora debe mostrar estado "APROBADO")
5. Deberia ver DOS botones:
   - "📋 Revisar" (izquierda)
   - "✓ Finalizar" (derecha) ← NUEVO!
6. Click en "✓ Finalizar"
```

### Paso 7: Completar la Finalizacion
```
1. Se abre modal "FINALIZAR REQUISICION"
2. Muestra:
   - Codigo: REQ-001
   - Solicitante: empleado1
   - Dependencia: [Departamento]
   - Total: $1,000.00
3. Ingresa observacion (opcional):
   "Productos entregados en perfecto estado"
4. Click en "✓ FINALIZAR REQUISICION"
5. Ver resultado:
   - Numero de historial: REQ-001-COMPLETO-15012025
   - Mensaje: "Requisicion finalizada correctamente"
   - Email enviado: SI
```

### Paso 8: Verificaciones Finales
```
✓ Status del dashboard cambió a COMPLETADO
✓ Boton "Finalizar" ya no aparece (estado no es APROBADO)
✓ Solicitante recibio email con PDF
✓ PDF abre correctamente en navegador
```

---

## TESTING VALIDACIONES

### Test 1: Usuario SIN rol EmpAlmacen
```
1. Login como: empleado1 (rol normal)
2. Ir a "REQUISICIONES"
3. Buscar REQ-001 (APROBADO)
4. Deberia NO ver boton "Finalizar"
   ✓ ESPERADO: Solo ve "Revisar"
```

### Test 2: Requisicion en estado PENDIENTE
```
1. Login como: emp_almacen
2. Crear nueva requisicion
3. Ir a requisiciones
4. Buscar la nueva (estado PENDIENTE)
5. Deberia NO ver boton "Finalizar"
   ✓ ESPERADO: Solo ve "Revisar"
```

### Test 3: Requisicion ya FINALIZADA
```
1. Login como: emp_almacen
2. Buscar REQ-001 (ya finalizado)
3. Deberia ver:
   - Status: COMPLETADO
   - Boton "Finalizar" desaparece
   - Boton "Revisar" sigue disponible
```

### Test 4: Email Notification
```
1. En paso 7 anterior, deberia ver "Email enviado: SI"
2. Abrir email del solicitante
3. Verificar:
   ✓ De: sistema@almacen.gob.py (o configurado)
   ✓ Asunto: "Requisición Completada: REQ-001"
   ✓ Cuerpo: HTML con logo SEDH
   ✓ PDF adjunto: "Requisicion_REQ-001_Completada.pdf"
```

### Test 5: PDF Content
```
1. Abrir PDF adjunto del email
2. Verificar contiene:
   ✓ Logo SEDH en encabezado
   ✓ Codigo: REQ-001
   ✓ Solicitante: [nombre]
   ✓ Dependencia: [nombre]
   ✓ Tabla de productos completa
   ✓ Total: $[monto]
   ✓ Numero de historial: REQ-001-COMPLETO-15012025
   ✓ Timestamps correctos
   ✓ Bloques de firma (5 espacios para firmas)
```

---

## TESTING AVANZADO

### Test 6: Caracteres Especiales
```
1. Crear requisicion con observacion:
   "Artículos especiales: café, año 2025, 100%"
2. Finalizar con comentario similar
3. Verificar en PDF:
   ✓ Caracteres acentuados aparecen correctamente
   ✓ Simbolos especiales (%, &, etc) funcionan
```

### Test 7: Numeros Grandes
```
1. Crear requisicion con productos costosos:
   - 100 x $10,000.00 = $1,000,000.00
2. Finalizar
3. Verificar en PDF y email:
   ✓ Totales calculados correctamente
   ✓ Formato de moneda correcto ($ 1,000,000.00)
```

### Test 8: Bajo Carga
```
1. Tener 10+ requisiciones en estado APROBADO
2. Como emp_almacen, finalizar 5 consecutivamente
3. Verificar:
   ✓ No hay timeouts
   ✓ Cada PDF se genera en <5 segundos
   ✓ Todos los emails se envían
   ✓ BD se actualiza correctamente
```

---

## TROUBLESHOOTING

### Problema: No veo el boton "Finalizar"
```
Causas posibles:
1. No soy usuario EmpAlmacen
   → Verificar rol: Admin > Usuarios > Perfil
   
2. Requisicion no esta en estado APROBADO
   → Verificar estado en columna "EstGeneral"
   → Esperar a que se completen todas las aprobaciones
   
3. Cache del navegador
   → Presionar Ctrl+Shift+Delete
   → Limpiar cookies y cache
   → Recargar pagina (Ctrl+F5)
```

### Problema: Modal se abre pero no puedo enviar
```
Causas posibles:
1. Navegador no soporta JavaScript
   → Verificar en consola (F12 > Console)
   → Cambiar navegador
   
2. Error de seguridad (CORS)
   → Revisar consola de desarrollador
   → Contactar al administrador
   
3. Servidor no responde
   → Verificar que http://192.168.180.164:8081 es accesible
   → Reiniciar servicio: systemctl restart almacen-backend
```

### Problema: Email no llega
```
Causas posibles:
1. SMTP no configurado correctamente
   → Revisar app/core/mail.py
   → Verificar credenciales
   → Probar conexion SMTP manualmente
   
2. Email del solicitante incorrecto
   → Verificar en tabla empleados
   → Asegurar formato valido (user@domain.com)
   
3. Email en carpeta SPAM
   → Buscar en carpeta Spam/Junk
   → Marcar como "No es Spam"
```

### Problema: PDF está vacio o no se genera
```
Causas posibles:
1. reportlab no instalado
   → En servidor ejecutar:
   source /opt/almacen-backend/.venv/bin/activate
   pip install reportlab
   
2. Archivo app/utils/pdf.py no existe
   → Verificar en /opt/almacen-backend/app/utils/
   → Si no existe, copiar de repositorio
   
3. Permisos de archivo
   → ls -la /opt/almacen-backend/app/utils/pdf.py
   → Deberia ser: -rw-r--r-- almacen almacen
```

---

## CHECKLIST FINAL

### Verificaciones de Seguridad
- [ ] Solo usuarios EmpAlmacen pueden finalizar
- [ ] Solo requisiciones APROBADO pueden finalizarse
- [ ] Email solo se envia al solicitante original
- [ ] Auditoria registra quien finalizo y cuando
- [ ] PDF no contiene datos sensibles adicionales

### Verificaciones Funcionales
- [ ] Boton "Finalizar" aparece en estado APROBADO
- [ ] Modal muestra datos correctos
- [ ] Numero de historial es formato correcto
- [ ] PDF se genera en <5 segundos
- [ ] Email se envia automaticamente
- [ ] Estado en BD cambia a COMPLETADO
- [ ] Notificacion aparece para solicitante

### Verificaciones de Datos
- [ ] Total en PDF coincide con suma de productos
- [ ] Aprobadores listados correctamente
- [ ] Fecha de finalizacion es actual
- [ ] Nombre del almacenero que finalizo es correcto
- [ ] Observaciones se guardan en BD

### Verificaciones de Performance
- [ ] Operacion toma < 10 segundos total
- [ ] PDF se genera < 5 segundos
- [ ] Email se envia asincrono (no bloquea)
- [ ] No hay menus de espera excessivos

---

## CONTACTO PARA ISSUES

Si encuentra algun problema:
1. Anotar el codigo de requisicion (ej: REQ-001)
2. Anotar hora exacta del problema
3. Screenshot del error (si aplica)
4. Revisar logs del servidor:
   ```
   ssh administrador@192.168.180.164
   journalctl -u almacen-backend -n 50
   ```
5. Contactar administrador con informacion

---

**Fecha:** 15 de enero de 2025
**Version:** 1.0
**Responsable:** Area de Almacen

