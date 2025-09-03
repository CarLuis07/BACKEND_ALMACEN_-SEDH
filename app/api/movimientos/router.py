from fastapi import APIRouter

router = APIRouter()

@router.get("/", summary="Listado de movimientos")
async def listar_movimientos():
    return []
