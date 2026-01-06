import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Ruta base de la aplicación
# En producción, se usa /opt/almacen-backend
# En desarrollo, se calcula dinámicamente
if os.path.exists("/opt/almacen-backend/app/frontend"):
    FRONTEND_BASE = "/opt/almacen-backend"
else:
    FRONTEND_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from threading import Thread
import time
from sqlalchemy import text
from app.core.database import SessionLocal
from app.core.mail import send_email

# Intentar importar los routers, si fallan, crear routers vacíos
try:
    from app.api.accesos.router import router as accesos_router
except ImportError:
    from fastapi import APIRouter
    accesos_router = APIRouter()

try:
    from app.api.productos.router import router as productos_router
except ImportError:
    from fastapi import APIRouter
    productos_router = APIRouter()

try:
    from app.api.requisiciones.router import router as requisiciones_router
except ImportError:
    from fastapi import APIRouter
    requisiciones_router = APIRouter()

try:
    from app.api.movimientos.router import router as movimientos_router
except ImportError:
    from fastapi import APIRouter
    movimientos_router = APIRouter()

try:
    from app.api.accesos.admin_router import router as admin_router
except ImportError:
    from fastapi import APIRouter
    admin_router = APIRouter()

try:
    from app.api.admin.router import router as admin_ui_router
except ImportError:
    from fastapi import APIRouter
    admin_ui_router = APIRouter()

try:
    from app.api.notificaciones.router import router as notificaciones_router
except ImportError:
    from fastapi import APIRouter
    notificaciones_router = APIRouter()

try:
    from app.api.permisos.router import router as permisos_router
except ImportError:
    from fastapi import APIRouter
    permisos_router = APIRouter()

app = FastAPI(
    title="Sistema de Almacén SEDH",
    description="API para el sistema de gestión de almacén de la SEDH",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especifica los dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir archivos estáticos del frontend
# Intentar montar desde /opt/almacen-backend/app/frontend
frontend_path = "/opt/almacen-backend/app/frontend" if os.path.exists("/opt/almacen-backend/app/frontend") else "app/frontend"
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")
    app.mount("/frontend", StaticFiles(directory=frontend_path), name="frontend")

# Incluir routers
app.include_router(accesos_router, prefix="/api/v1/accesos", tags=["accesos"])
app.include_router(productos_router, prefix="/api/v1/productos", tags=["productos"])
app.include_router(requisiciones_router, prefix="/api/v1/requisiciones", tags=["requisiciones"])
app.include_router(movimientos_router, prefix="/api/v1/movimientos", tags=["movimientos"])
app.include_router(admin_router, prefix="/api/v1/admin-legacy", tags=["administracion-legacy"])  # Router viejo renombrado
app.include_router(admin_ui_router)  # Ya tiene su propio prefix /api/v1/admin - ROUTER NUEVO
app.include_router(notificaciones_router, prefix="/api/v1/notificaciones", tags=["notificaciones"])
app.include_router(permisos_router, prefix="/api/v1/permisos", tags=["permisos"])

# Función auxiliar para servir archivos frontend
def get_frontend_file(filename: str):
    """Obtiene la ruta absoluta de un archivo del frontend"""
    # Intentar primero la ruta de producción
    file_path = f"/opt/almacen-backend/app/frontend/{filename}"
    if not os.path.exists(file_path):
        # Si no existe, intentar ruta relativa de desarrollo
        file_path = f"app/frontend/{filename}"
    
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="text/html; charset=utf-8")
    
    # Si no existe en ningún lado, retornar error
    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail=f"Archivo {filename} no encontrado")

@app.get("/")
async def root():
    """Servir la página principal de login"""
    return get_frontend_file("index.html")

@app.get("/api")
async def api_info():
    """Información de la API"""
    return {"message": "API del Sistema de Almacén SEDH", "version": "1.0.0"}

@app.get("/login")
async def login_page():
    """Servir la página de login (alias de la página principal)"""
    return get_frontend_file("index.html")

@app.get("/dashboard")
async def dashboard():
    """Servir la página del dashboard"""
    return get_frontend_file("dashboard.html")

@app.get("/productos")
async def productos_page():
    """Servir la página de productos"""
    return get_frontend_file("productos.html")

@app.get("/agregar-producto")
async def agregar_producto_page():
    """Servir la página para agregar productos"""
    return get_frontend_file("agregar-producto.html")

@app.get("/requisiciones")
async def requisiciones_page():
    """Servir la página de requisiciones"""
    return get_frontend_file("requisiciones.html")

@app.get("/categorias")
async def categorias_page():
    """Servir la página de categorías"""
    return get_frontend_file("categorias.html")

@app.get("/mis-requisiciones")
async def mis_requisiciones_page():
    """Servir la página de mis requisiciones personales"""
    return get_frontend_file("mis-requisiciones.html")

@app.get("/historial")
async def historial_page():
    """Servir la página de historial de requisiciones"""
    return get_frontend_file("historial.html")

@app.get("/control-almacen")
async def control_almacen_page():
    """Servir la página de control de almacén"""
    return get_frontend_file("control-almacen.html")

@app.get("/reportes")
async def reportes_page():
    """Servir la página de reportes para auditor (original)"""
    return get_frontend_file("reportes-auditor.html")

@app.get("/reportes-completo")
async def reportes_completo_page():
    """Servir la página de reportes completos mejorados"""
    return get_frontend_file("reportes-completo.html")

@app.get("/asignar-modulos")
async def asignar_modulos_page():
    """Servir la página de asignación de módulos personalizados"""
    return get_frontend_file("asignar-modulos.html")

@app.get("/admin")
async def admin_page():
    """Servir la página de administración (permisos de módulos)"""
    return get_frontend_file("admin.html")

@app.get("/admin/usuarios")
async def admin_usuarios_page():
    """Servir la página de administración de usuarios (módulo dedicado)"""
    html_path = os.path.join(os.path.dirname(__file__), "api", "admin", "admin.html")
    return FileResponse(html_path)

# Rutas para el Sistema Avanzado de Movimientos
@app.get("/movimientos-dashboard")
async def movimientos_dashboard_page():
    """Servir la página del Dashboard de Movimientos Interactivo"""
    return get_frontend_file("movimientos-dashboard.html")

@app.get("/movimientos-trazabilidad")
async def movimientos_trazabilidad_page():
    """Servir la página de Trazabilidad de Productos"""
    return get_frontend_file("movimientos-trazabilidad.html")

@app.get("/movimientos-alertas")
async def movimientos_alertas_page():
    """Servir la página del Sistema de Alertas Inteligentes"""
    return get_frontend_file("movimientos-alertas.html")

@app.get("/movimientos-inventario")
async def movimientos_inventario_page():
    """Servir la página del Módulo de Inventario Físico"""
    return get_frontend_file("movimientos-inventario.html")

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Sistema funcionando correctamente"}

@app.get("/email-log")
async def email_log_page():
    """Servir la página de visualización de logs de correo"""
    return get_frontend_file("email-log.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)

# ================================
# Background job: envío de notificaciones por correo
# ================================

def _notificaciones_sender_loop():
    enabled = os.getenv("NOTIF_SENDER_ENABLED", "false").lower() in ("1", "true", "yes")
    interval = int(os.getenv("NOTIF_SENDER_INTERVAL_SEC", "120"))
    if not enabled:
        return
    while True:
        try:
            db = SessionLocal()
            # Seleccionar hasta 100 pendientes globales para evitar duplicaciones masivas
            q = text("""
                SELECT n.idnotificacion, n.emailusuario, n.tipo, n.mensaje, r.codrequisicion
                FROM requisiciones.notificaciones n
                LEFT JOIN requisiciones.requisiciones r ON r.idrequisicion = n.idrequisicion
                WHERE (n.estado_envio IS NULL OR n.estado_envio <> 'enviado')
                ORDER BY n.fechacreacion ASC
                LIMIT 100
            """)
            rows = db.execute(q).fetchall()

            for idnotif, emailusuario, tipo, mensaje, codreq in rows:
                subject = f"[SEDH Almacén] Notificación: {tipo}"
                body = mensaje
                if codreq:
                    body += f"\n\nCódigo: {codreq}"

                estado, error = send_email(emailusuario, subject, body)
                if estado == "enviado":
                    db.execute(text("""
                        UPDATE requisiciones.notificaciones
                        SET estado_envio='enviado', medio=COALESCE(medio,'smtp'), enviado_en=NOW(), error_envio=NULL
                        WHERE idnotificacion=:id
                    """), {"id": idnotif})
                else:
                    db.execute(text("""
                        UPDATE requisiciones.notificaciones
                        SET estado_envio='error', medio=COALESCE(medio,'smtp'), enviado_en=NOW(), error_envio=:err
                        WHERE idnotificacion=:id
                    """), {"id": idnotif, "err": error or "Error desconocido"})
            db.commit()
        except Exception:
            try:
                db.rollback()
            except Exception:
                pass
        finally:
            try:
                db.close()
            except Exception:
                pass
        time.sleep(interval)

@app.on_event("startup")
async def _startup_notif_sender():
    # Nota: en producción con múltiples workers, este hilo se iniciará por worker.
    # Para evitar envíos duplicados, usar un único worker o mover este job a un proceso dedicado.
    t = Thread(target=_notificaciones_sender_loop, daemon=True)
    t.start()