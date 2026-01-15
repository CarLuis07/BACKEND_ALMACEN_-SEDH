#!/usr/bin/env python3
"""Verificar imports del router"""

import paramiko

SERVER = "192.168.180.164"
USER = "administrador"  
PASSWORD = "DHumanos25"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(SERVER, username=USER, password=PASSWORD, allow_agent=False, look_for_keys=False)

# Verificar que el router se puede importar
test_script = '''import sys
sys.path.insert(0, '/opt/almacen-backend')

try:
    print("Intentando importar router de requisiciones...")
    from app.api.requisiciones import router
    print("✓ Import exitoso")
    
    print("\\nVerificando funciones de notificaciones...")
    funcs = [
        'api_listar_notificaciones',
        'api_marcar_notif_leida',
        'api_marcar_todas_leidas',
        'api_enviar_notificaciones_pendientes'
    ]
    
    router_obj = router.router
    for func_name in funcs:
        # Buscar en las rutas del router
        found = False
        for route in router_obj.routes:
            if hasattr(route, 'endpoint') and route.endpoint.__name__ == func_name:
                print(f"  ✓ {func_name} encontrado en rutas")
                found = True
                break
        if not found:
            print(f"  ✗ {func_name} NO encontrado en rutas")
    
    print(f"\\nTotal rutas en requisiciones.router: {len(router_obj.routes)}")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
'''

# Crear archivo y ejecutar
stdin, stdout, stderr = client.exec_command(
    "cat > /tmp/test_import.py << 'EOF'\n" + test_script + "\nEOF\n" +
    "/opt/almacen-backend/venv/bin/python3 /tmp/test_import.py"
)

output = stdout.read().decode()
error = stderr.read().decode()

print(output)

if error:
    print("\nErrores:")
    print(error)

client.close()
