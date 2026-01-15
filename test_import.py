#!/usr/bin/env python3
import sys
sys.path.insert(0, '/opt/almacen-backend')

try:
    from app.repositories.requisiciones import responder_requisicion_almacen
    print("✓ Import successful")
except Exception as e:
    print(f"✗ Import failed: {e}")
    import traceback
    traceback.print_exc()
