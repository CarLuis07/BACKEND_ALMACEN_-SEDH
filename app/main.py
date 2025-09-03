from fastapi import FastAPI
from app.core.config import settings
from app.api.accesos.router import router as accesos_router
from app.api.productos.router import router as productos_router
from app.api.requisiciones.router import router as requisiciones_router
from app.core.database import test_db_connection

app = FastAPI(title=settings.PROJECT_NAME)

app.include_router(accesos_router, prefix=f"{settings.API_V1_PREFIX}/accesos", tags=["accesos"])
app.include_router(productos_router, prefix=f"{settings.API_V1_PREFIX}/productos", tags=["productos"])
app.include_router(requisiciones_router, prefix=f"{settings.API_V1_PREFIX}/requisiciones", tags=["requisiciones"])

@app.get("/")
def root():
    return {"message": "API Almacén SEDH"}

@app.get(f"{settings.API_V1_PREFIX}/health/db")
def health_db():
    ok, msg = test_db_connection()
    return {"database": "up" if ok else "down", "detail": msg}