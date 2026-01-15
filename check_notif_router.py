#!/opt/almacen-backend/venv/bin/python3
import sys
sys.path.insert(0, "/opt/almacen-backend")
try:
    from app.api.notificaciones.router import router
    print(f"✓ Router imported: {len(router.routes)} routes")
except Exception as e:
    print(f"✗ Error importing router: {e}")
    import traceback
    traceback.print_exc()
