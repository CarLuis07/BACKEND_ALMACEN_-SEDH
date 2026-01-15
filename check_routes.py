from app.main import app
from fastapi.routing import APIRoute

notif_routes = []
for route in app.routes:
    if isinstance(route, APIRoute):
        if 'notificaciones' in route.path:
            notif_routes.append(route.path)

print(f"Total routes: {len(app.routes)}")
print(f"Notificaciones routes: {notif_routes}")

# Ver si el router está incluido
for i, route in enumerate(app.routes):
    try:
        if hasattr(route, 'path') and '/api/v1' in route.path:
            print(f"{i}: {route.path}")
    except:
        pass
