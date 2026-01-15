# DEPLOYMENT MANUAL DE NOTIFICACIONES
# ====================================

## Cambios realizados:

1. **app/api/requisiciones/router.py** (Líneas 2806-2978)
   - Agregados 3 endpoints proxy para servir funcionalidad de notificaciones
   - GET /notificaciones: Lista notificaciones del usuario
   - PUT /notificaciones/{id_notificacion}/marcar-leida: Marca como leída
   - PUT /notificaciones/marcar-todas-leidas: Marca todas como leídas
   - POST /notificaciones/enviar-pendientes: Envía notificaciones pendientes

2. **app/frontend/dashboard.html**
   - Actualizado loadNotifications() para llamar a /api/v1/requisiciones/notificaciones
   - Actualizado marcarNotificacionLeida() para llamar a /api/v1/requisiciones/notificaciones/{id}/marcar-leida
   - Actualizado marcarTodasLeidas() para llamar a /api/v1/requisiciones/notificaciones/marcar-todas-leidas
   - Actualizado enviarNotificacionesPendientes() para llamar a /api/v1/requisiciones/notificaciones/enviar-pendientes

## Pasos para desplegar:

### Opción 1: Via Git (recomendado)
```bash
cd /opt/almacen-backend
git pull origin main
systemctl restart almacen-backend
sleep 3
systemctl is-active almacen-backend
curl -X GET "http://127.0.0.1:8081/api/v1/requisiciones/notificaciones?solo_no_leidas=false" \
    -H "Authorization: Bearer test"
```

### Opción 2: Copiar archivos manualmente
```bash
# En el servidor
scp usuario@CLIENTE:/ruta/app/api/requisiciones/router.py /opt/almacen-backend/app/api/requisiciones/
scp usuario@CLIENTE:/ruta/app/frontend/dashboard.html /opt/almacen-backend/app/frontend/

systemctl restart almacen-backend
sleep 3
systemctl is-active almacen-backend
```

## Verificación

El endpoint debe responder con los siguientes cambios:

1. Dashboard debe cargar sin error 404 en notificaciones
2. El bell icon debe mostrar notificaciones sin errores
3. Marcar como leída debe actualizar el estado
4. Marcar todas como leídas debe actualizar todos

## Rollback (si es necesario)

```bash
cd /opt/almacen-backend
git revert fbc6788  # commit del deployment
systemctl restart almacen-backend
```

## Logs para verificación

```bash
# Ver logs del servicio
journalctl -u almacen-backend -n 50 -f

# Ver errores específicos
grep "ERROR" /var/log/almacen-backend.log
```
