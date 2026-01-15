#!/bin/bash
# Script para verificar y diagnosticar el deployment

echo "======================================================"
echo "DIAGNÓSTICO POST-DEPLOYMENT"
echo "======================================================"

echo ""
echo "1. Verificando archivos copiados..."
if [ -f "/opt/almacen-backend/app/api/requisiciones/router.py" ]; then
    SIZE=$(wc -l < /opt/almacen-backend/app/api/requisiciones/router.py)
    echo "✓ router.py existe (${SIZE} líneas)"
    
    # Buscar el endpoint proxy
    if grep -q "def api_listar_notificaciones" /opt/almacen-backend/app/api/requisiciones/router.py; then
        echo "  ✓ Endpoint api_listar_notificaciones encontrado"
    else
        echo "  ✗ Endpoint api_listar_notificaciones NO encontrado"
    fi
else
    echo "✗ router.py NO existe"
fi

echo ""
echo "2. Verificando servicio..."
STATUS=$(systemctl is-active almacen-backend)
echo "   Estado: $STATUS"

if [ "$STATUS" = "active" ]; then
    echo "   ✓ Servicio activo"
else
    echo "   ✗ Servicio no activo"
    echo "   Últimos errores:"
    journalctl -u almacen-backend -n 5 --no-pager | grep -i "error\|failed" || echo "   (sin errores identificables)"
fi

echo ""
echo "3. Probando endpoint..."
RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "http://127.0.0.1:8081/api/v1/requisiciones/notificaciones" -H "Authorization: Bearer test" 2>&1)
HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
BODY=$(echo "$RESPONSE" | head -n -1)

echo "   HTTP Code: $HTTP_CODE"
echo "   Response: ${BODY:0:100}..."

if [ "$HTTP_CODE" = "401" ] || [ "$HTTP_CODE" = "200" ]; then
    echo "   ✓ Endpoint responde"
elif [ "$HTTP_CODE" = "404" ]; then
    echo "   ✗ Endpoint retorna 404 (no encontrado)"
    echo ""
    echo "4. Listando rutas registradas..."
    python3 -c "
import sys
sys.path.insert(0, '/opt/almacen-backend')
from app.main import app
print('Rutas en la app:')
for route in app.routes:
    if 'notificaciones' in str(route.path).lower():
        print(f'  - {route.path} ({route.methods})')
" 2>&1 | head -20 || echo "   (no se pudo listar)"
else
    echo "   ✗ Error HTTP $HTTP_CODE"
fi

echo ""
echo "5. Verificando imports..."
python3 -c "
import sys
sys.path.insert(0, '/opt/almacen-backend')
try:
    from app.api.requisiciones import router
    print('✓ Router de requisiciones importa correctamente')
    
    # Verificar que tiene el endpoint
    if hasattr(router, 'api_listar_notificaciones'):
        print('✓ Función api_listar_notificaciones existe')
    else:
        print('✗ Función api_listar_notificaciones NO existe')
except Exception as e:
    print(f'✗ Error importando router: {e}')
" 2>&1

echo ""
echo "======================================================"
echo "FIN DEL DIAGNÓSTICO"
echo "======================================================"
