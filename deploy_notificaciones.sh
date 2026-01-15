#!/bin/bash
# Script de deployment de notificaciones para almacen-backend
# Ejecutar en el servidor: bash deploy_notificaciones.sh

set -e

echo "=========================================="
echo "DEPLOYMENT: Actualización de Notificaciones"
echo "=========================================="

cd /opt/almacen-backend

echo ""
echo "1. Sincronizando con GitHub..."
git pull origin main

echo ""
echo "2. Reiniciando servicio almacen-backend..."
systemctl restart almacen-backend

echo ""
echo "3. Esperando a que inicie el servicio..."
sleep 3

echo ""
echo "4. Verificando estado del servicio..."
STATUS=$(systemctl is-active almacen-backend)
if [ "$STATUS" = "active" ]; then
    echo "✓ Servicio activo"
else
    echo "✗ Servicio no activo: $STATUS"
    systemctl status almacen-backend
    exit 1
fi

echo ""
echo "5. Probando endpoint de notificaciones..."
RESPONSE=$(curl -s -X GET "http://127.0.0.1:8081/api/v1/requisiciones/notificaciones?solo_no_leidas=false" \
    -H "Authorization: Bearer test" -w "\n%{http_code}" 2>&1)

HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
BODY=$(echo "$RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "401" ]; then
    echo "✓ Endpoint responde: HTTP $HTTP_CODE"
    echo "  Respuesta: ${BODY:0:100}..."
else
    echo "✗ Endpoint error: HTTP $HTTP_CODE"
    echo "  Respuesta: $BODY"
fi

echo ""
echo "=========================================="
echo "✓ DEPLOYMENT COMPLETADO EXITOSAMENTE"
echo "=========================================="
