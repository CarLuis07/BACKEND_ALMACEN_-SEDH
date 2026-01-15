from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user

router = APIRouter()


def _is_admin(user: dict) -> bool:
    rol = (user or {}).get("rol") or (user or {}).get("role") or ""
    return "admin" in str(rol).lower()


async def _get_notificaciones(
    solo_no_leidas: bool,
    codigo: Optional[str],
    todas: bool,
    db: Session,
    current_user: dict,
):
    """Lógica compartida para listar notificaciones"""
    email = (current_user or {}).get("sub") or (current_user or {}).get("email")
    if not email and not (todas and _is_admin(current_user)):
        raise HTTPException(status_code=401, detail="No autenticado")

    filtros: List[str] = []
    params = {}

    if not (todas and _is_admin(current_user)):
        filtros.append("LOWER(n.emailusuario) = LOWER(:email)")
        params["email"] = email

    if solo_no_leidas:
        filtros.append("COALESCE(n.leida, FALSE) = FALSE")

    if codigo:
        filtros.append("LOWER(r.codrequisicion) LIKE LOWER(:codigo)")
        params["codigo"] = f"%{codigo}%"

    query = (
        "SELECT n.idnotificacion, n.tipo, n.mensaje, n.leida, n.fechacreacion, "
        "n.emailusuario, n.estado_envio, n.medio, n.enviado_en, n.error_envio, "
        "n.idrequisicion, COALESCE(r.codrequisicion, '') AS codrequisicion "
        "FROM requisiciones.notificaciones n "
        "LEFT JOIN requisiciones.requisiciones r ON r.idrequisicion = n.idrequisicion "
    )

    if filtros:
        query += " WHERE " + " AND ".join(filtros)

    query += " ORDER BY n.fechacreacion DESC LIMIT 200"

    rows = db.execute(text(query), params).mappings().all()
    data = [dict(row) for row in rows]
    total = len(data)
    no_leidas = sum(1 for r in data if not r.get("leida"))

    return {"notificaciones": data, "total": total, "noLeidas": no_leidas}


@router.get("/test")
async def test_endpoint():
    return {"status": "notificaciones router is loaded"}


@router.get("")
async def listar_notificaciones_sin_slash(
    solo_no_leidas: bool = False,
    codigo: Optional[str] = None,
    todas: bool = False,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await _get_notificaciones(solo_no_leidas, codigo, todas, db, current_user)


@router.get("/")
async def listar_notificaciones(
    solo_no_leidas: bool = False,
    codigo: Optional[str] = None,
    todas: bool = False,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await _get_notificaciones(solo_no_leidas, codigo, todas, db, current_user)


@router.put("/{id_notificacion}/marcar-leida", summary="Marca una notificación como leída")
async def marcar_leida(
    id_notificacion: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    email = (current_user or {}).get("sub") or (current_user or {}).get("email")
    es_admin = _is_admin(current_user)
    if not email and not es_admin:
        raise HTTPException(status_code=401, detail="No autenticado")

    res = db.execute(
        text(
            """
            UPDATE requisiciones.notificaciones
            SET leida = TRUE
            WHERE idnotificacion = CAST(:id AS UUID)
              AND (LOWER(emailusuario) = LOWER(:email) OR :es_admin)
            RETURNING idnotificacion
            """
        ),
        {"id": id_notificacion, "email": email or "", "es_admin": es_admin},
    ).fetchone()

    db.commit()

    if not res:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")

    return {"status": "ok"}


@router.put("/marcar-todas-leidas", summary="Marca todas las notificaciones del usuario como leídas")
async def marcar_todas_leidas(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    email = (current_user or {}).get("sub") or (current_user or {}).get("email")
    if not email:
        raise HTTPException(status_code=401, detail="No autenticado")

    db.execute(
        text(
            """
            UPDATE requisiciones.notificaciones
            SET leida = TRUE
            WHERE LOWER(emailusuario) = LOWER(:email)
            """
        ),
        {"email": email},
    )
    db.commit()
    return {"status": "ok"}


@router.post("/enviar-pendientes", summary="Dispara el envío de notificaciones pendientes")
async def enviar_pendientes():
    # El envío real lo hace el worker en background; aquí solo respondemos 200 OK
    return {"status": "ok", "detalle": "Worker en background manejando el envío"}
