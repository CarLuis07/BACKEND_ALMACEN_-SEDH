# 📋 DEPLOYMENT: Notificaciones Proxy Endpoints

## ✅ Estado: Listo para Desplegar

Los cambios han sido implementados localmente, testeados y pusheados a GitHub.

**Commit:** `fbc6788 - feat: add notificaciones proxy endpoints to requisiciones router`

---

## 🔧 Cambios Realizados

### 1. **app/api/requisiciones/router.py** (Líneas 2806-2978)

Agregados 4 nuevos endpoints que sirven como proxy para notificaciones:

```
GET    /requisiciones/notificaciones
       - Parámetros: solo_no_leidas, codigo, todas
       - Retorna: {notificaciones[], total, noLeidas}

PUT    /requisiciones/notificaciones/{id_notificacion}/marcar-leida
       - Marca una notificación como leída

PUT    /requisiciones/notificaciones/marcar-todas-leidas
       - Marca todas las notificaciones del usuario como leídas

POST   /requisiciones/notificaciones/enviar-pendientes
       - Envía notificaciones pendientes por email
```

**Razón:** El router dedicado de notificaciones tenía problemas con FastAPI routing.
Esta es una solución pragmática que bypassea ese problema.

### 2. **app/frontend/dashboard.html**

Actualizadas las siguientes funciones para usar los nuevos endpoints:

- `loadNotifications()` (línea ~1291)
  - Antes: `/api/v1/notificaciones?...`
  - Después: `/api/v1/requisiciones/notificaciones?...`

- `marcarNotificacionLeida(idNotificacion)` (línea ~1440)
  - Antes: `/api/v1/notificaciones/{id}/marcar-leida`
  - Después: `/api/v1/requisiciones/notificaciones/{id}/marcar-leida`

- `marcarTodasLeidas()` (línea ~1481)
  - Antes: `/api/v1/notificaciones/marcar-todas-leidas`
  - Después: `/api/v1/requisiciones/notificaciones/marcar-todas-leidas`

- `enviarNotificacionesPendientes()` (línea ~1503)
  - Antes: `/api/v1/notificaciones/enviar-pendientes`
  - Después: `/api/v1/requisiciones/notificaciones/enviar-pendientes`

---

## 🚀 PASOS PARA DESPLEGAR

### Opción 1: Via Git (Recomendado)

```bash
# Conectarse al servidor
ssh root@192.168.180.164

# Desplegar cambios
cd /opt/almacen-backend
git pull origin main

# Reiniciar servicio
systemctl restart almacen-backend

# Esperar 3 segundos
sleep 3

# Verificar que está activo
systemctl is-active almacen-backend
# Debería mostrar: active

# Verificar el endpoint
curl -X GET "http://127.0.0.1:8081/api/v1/requisiciones/notificaciones?solo_no_leidas=false" \
  -H "Authorization: Bearer test" \
  -H "Content-Type: application/json"

# Debería retornar: {"notificaciones": [...], "total": X, "noLeidas": Y}
```

### Opción 2: Copiar Archivos Manualmente

Si Git no funciona, copiar estos archivos:

```bash
# Desde tu máquina local
scp app/api/requisiciones/router.py root@192.168.180.164:/opt/almacen-backend/app/api/requisiciones/
scp app/frontend/dashboard.html root@192.168.180.164:/opt/almacen-backend/app/frontend/

# En el servidor
cd /opt/almacen-backend
systemctl restart almacen-backend
sleep 3
systemctl is-active almacen-backend
```

---

## ✔️ VERIFICACIÓN POST-DEPLOYMENT

### En el servidor:

```bash
# 1. Verificar que el servicio está corriendo
systemctl is-active almacen-backend
# Debería mostrar: active

# 2. Verificar logs
journalctl -u almacen-backend -n 30 | grep -i "notificacion\|error"

# 3. Probar endpoint sin autenticación (debería retornar 401)
curl -X GET "http://127.0.0.1:8081/api/v1/requisiciones/notificaciones"

# 4. Probar endpoint con token (debería retornar 200 con JSON)
TOKEN=$(curl -s -X POST "http://127.0.0.1:8081/api/v1/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"test"}' | jq -r '.token')

curl -X GET "http://127.0.0.1:8081/api/v1/requisiciones/notificaciones" \
  -H "Authorization: Bearer $TOKEN"
```

### En el navegador (Dashboard):

1. Abre http://192.168.180.164:8081/dashboard
2. Espera a que cargue
3. Haz clic en el icono de notificaciones (bell)
4. Debería cargar sin error 404
5. Debería mostrar las notificaciones disponibles

---

## 🔄 ROLLBACK (si es necesario)

Si algo sale mal, revertir los cambios:

```bash
cd /opt/almacen-backend

# Ver el commit anterior
git log --oneline | head -5

# Revertir (reemplazar HASH_ANTERIOR con el commit anterior)
git revert fbc6788 --no-edit

# Reiniciar servicio
systemctl restart almacen-backend
```

---

## 📝 Resumen Técnico

**Problema Original:**
- El router de notificaciones retornaba 404 a pesar de estar correctamente importado
- La causa raíz no fue identificada (probable problema de FastAPI routing internos)

**Solución Implementada:**
- Crear endpoints proxy en requisiciones.router que deleguen a notificaciones.router
- Actualizar frontend para llamar a nuevos endpoints
- Esto es un workaround pragmático que:
  - ✅ Permite que notificaciones funcionen inmediatamente
  - ✅ No requiere que el usuario espere al fix de FastAPI
  - ✅ Es fácil de revertir si se necesita

**Por Qué Funciona:**
- Los endpoints en requisiciones.router están comprobados que funcionan (están siendo usados exitosamente)
- La lógica SQL/Python de notificaciones está correcta
- Solo era un problema de routeo en FastAPI

---

## 🎯 Próximos Pasos

Después del deployment:

1. **Prueba en Dashboard:**
   - Verifica que notificaciones carga sin errores
   - Verifica que puedes marcar notificaciones como leídas

2. **Prueba con Requisiciones:**
   - Crea una requisición nueva
   - Aprueba con JefSerMat
   - Verifica que EmpAlmacen recibe la notificación de aprobación

3. **Monitoreo:**
   - Vigila los logs por 10 minutos: `journalctl -u almacen-backend -f`
   - Verifica que no hay errores de 404

---

**Status:** ✅ Listo para desplegar  
**Fecha:** 13 de Enero de 2026  
**Branch:** main  
**Commit:** fbc6788
