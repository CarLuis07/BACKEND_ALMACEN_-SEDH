import sys
sys.path.insert(0, "/opt/almacen-backend")

try:
    from app.api.notificaciones.router import router
    print("✓ Router imported successfully")
    print(f"✓ Routes count: {len(router.routes)}")
    for r in router.routes:
        print(f"  - {r.path} {r.methods if hasattr(r, 'methods') else ''}")
except Exception as e:
    print(f"✗ Import failed: {e}")
    import traceback
    traceback.print_exc()
