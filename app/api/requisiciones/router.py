from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import ProgrammingError, SQLAlchemyError

from app.core.database import get_db
from app.core.security import get_current_user
from app.repositories.requisiciones import crear_requisicion, requisiciones_pendientes_jefe, responder_requisicion_jefe
from app.repositories.requisiciones import requisiciones_pendientes_gerente
from app.repositories.requisiciones import responder_requisicion_gerente
from app.repositories.requisiciones import requisiciones_pendientes_jefe_materiales
from app.repositories.requisiciones import responder_requisicion_jefe_materiales
from app.repositories.requisiciones import requisiciones_pendientes_almacen
from app.repositories.requisiciones import responder_requisicion_almacen
from app.schemas.requisiciones.schemas import CrearRequisicionIn, CrearRequisicionOut, ResponderRequisicionIn, ResponderRequisicionOut
from app.schemas.requisiciones.schemas import RequisicionPendienteOut
from app.schemas.requisiciones.schemas import RequisicionPendienteGerenteOut
from app.schemas.requisiciones.schemas import ResponderRequisicionGerenteIn

#EMPLEADOS 
router = APIRouter()
@router.post("/", summary="Crear requisición", response_model=CrearRequisicionOut)
@router.post("", include_in_schema=False)
async def api_crear_requisicion(
    body: CrearRequisicionIn,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    email = (str(current_user.get("email") or current_user.get("sub") or "")).strip()
    if not email:
        raise HTTPException(status_code=401, detail="No se encontró email del usuario autenticado")
    body = body.model_copy(update={"email": email})
    return crear_requisicion(db, body)

# JEFES INMEDIATOS
@router.get(
    "/pendientes/jefe",
    summary="Listar requisiciones pendientes del jefe inmediato",
    response_model=list[RequisicionPendienteOut],
)
async def api_requisiciones_pendientes_jefe(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    email = (str(current_user.get("email") or current_user.get("sub") or "")).strip()
    if not email:
        raise HTTPException(status_code=401, detail="No se encontró email del usuario autenticado")

    try:
        return requisiciones_pendientes_jefe(db, email)
    except ProgrammingError as e:
        msg = str(getattr(e, "orig", e))
        if "Usuario no autorizado" in msg or "no es Jefe Inmediato" in msg:
            raise HTTPException(status_code=401, detail="Usuario no autorizado: no es Jefe Inmediato")
        raise HTTPException(status_code=500, detail="Error al consultar requisiciones pendientes")
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Error de base de datos")
    except Exception:
        raise HTTPException(status_code=500, detail="Error inesperado")


@router.post(
    "/responder/jefe",
    summary="Responder (aprobar/rechazar) una requisición de un subordinado",
    response_model=ResponderRequisicionOut,
)
async def api_responder_requisicion_jefe(
    body: ResponderRequisicionIn,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    email = (str(current_user.get("email") or current_user.get("sub") or "")).strip()
    if not email:
        raise HTTPException(status_code=401, detail="No se encontró email del usuario autenticado")

    try:
        return responder_requisicion_jefe(db, body, email)
    except ProgrammingError as e:
        msg = str(getattr(e, "orig", e))
        if "Usuario no autorizado" in msg or "no es Jefe Inmediato" in msg:
            raise HTTPException(status_code=401, detail="Usuario no autorizado: no es Jefe Inmediato")
        if "Estado inválido" in msg or "Comentario es obligatorio" in msg:
            raise HTTPException(status_code=400, detail=msg)
        raise HTTPException(status_code=500, detail="Error al responder la requisición")
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Error de base de datos")
    except Exception:
        raise HTTPException(status_code=500, detail="Error inesperado")

# GERENTES ADMINISTRATIVOS
@router.get(
    "/pendientes/gerente",
    summary="Listar requisiciones pendientes del Gerente Administrativo",
    response_model=list[RequisicionPendienteGerenteOut],
)
async def api_requisiciones_pendientes_gerente(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    email = (str(current_user.get("email") or current_user.get("sub") or "")).strip()
    if not email:
        raise HTTPException(status_code=401, detail="No se encontró email del usuario autenticado")

    try:
        return requisiciones_pendientes_gerente(db, email)
    except ProgrammingError as e:
        msg = str(getattr(e, "orig", e))
        if "Usuario no autorizado" in msg or "no es Gerente Administrativo" in msg:
            raise HTTPException(status_code=401, detail="Usuario no autorizado: no es Gerente Administrativo")
        raise HTTPException(status_code=500, detail="Error al consultar requisiciones pendientes (gerente)")
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Error de base de datos")
    except Exception:
        raise HTTPException(status_code=500, detail="Error inesperado")


@router.post(
    "/responder/gerente",
    summary="Gerente Administrativo responde (aprobar/rechazar) una requisición",
    response_model=ResponderRequisicionOut,
)
async def api_responder_requisicion_gerente(
    body: ResponderRequisicionGerenteIn,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    email = (str(current_user.get("email") or current_user.get("sub") or "")).strip()
    if not email:
        raise HTTPException(status_code=401, detail="No se encontró email del usuario autenticado")

    try:
        return responder_requisicion_gerente(db, body, email)
    except ProgrammingError as e:
        msg = str(getattr(e, "orig", e))
        if "Usuario no autorizado" in msg or "no es Gerente Administrativo" in msg:
            raise HTTPException(status_code=401, detail="Usuario no autorizado: no es Gerente Administrativo")
        if "Estado inválido" in msg or "Comentario es obligatorio" in msg:
            raise HTTPException(status_code=400, detail=msg)
        raise HTTPException(status_code=500, detail="Error al responder la requisición")
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Error de base de datos")
    except Exception:
        raise HTTPException(status_code=500, detail="Error inesperado")

# JEFES DE MATERIALES
@router.get(
    "/pendientes/jefe-materiales",
    summary="Listar requisiciones pendientes del Jefe de Materiales",
    response_model=list[RequisicionPendienteGerenteOut],
)
async def api_requisiciones_pendientes_jefe_materiales(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    email = (str(current_user.get("email") or current_user.get("sub") or "")).strip()
    if not email:
        raise HTTPException(status_code=401, detail="No se encontró email del usuario autenticado")

    try:
        return requisiciones_pendientes_jefe_materiales(db, email)
    except ProgrammingError as e:
        msg = str(getattr(e, "orig", e))
        if "Usuario no autorizado" in msg or "no es Jefe de Materiales" in msg:
            raise HTTPException(status_code=401, detail="Usuario no autorizado: no es Jefe de Materiales")
        raise HTTPException(status_code=500, detail="Error al consultar requisiciones pendientes (jefe de materiales)")
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Error de base de datos")
    except Exception:
        raise HTTPException(status_code=500, detail="Error inesperado")


@router.post(
    "/responder/jefe-materiales",
    summary="Jefe de Materiales responde (aprobar/rechazar) una requisición",
    response_model=ResponderRequisicionOut,
)
async def api_responder_requisicion_jefe_materiales(
    body: ResponderRequisicionGerenteIn,  # reutiliza el esquema del gerente
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    email = (str(current_user.get("email") or current_user.get("sub") or "")).strip()
    if not email:
        raise HTTPException(status_code=401, detail="No se encontró email del usuario autenticado")

    try:
        return responder_requisicion_jefe_materiales(db, body, email)
    except ProgrammingError as e:
        msg = str(getattr(e, "orig", e))
        if "Usuario no autorizado" in msg or "no es Jefe de Materiales" in msg:
            raise HTTPException(status_code=401, detail="Usuario no autorizado: no es Jefe de Materiales")
        if "Estado inválido" in msg or "Comentario es obligatorio" in msg or "no puede aumentar la cantidad" in msg:
            raise HTTPException(status_code=400, detail=msg)
        raise HTTPException(status_code=500, detail="Error al responder la requisición (jefe de materiales)")
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Error de base de datos")
    except Exception:
        raise HTTPException(status_code=500, detail="Error inesperado")

# EMPLEADOS ALMACEN
@router.get(
    "/pendientes/almacen",
    summary="Listar requisiciones pendientes del Empleado de Almacén",
    response_model=list[RequisicionPendienteGerenteOut],
)
async def api_requisiciones_pendientes_almacen(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    email = (str(current_user.get("email") or current_user.get("sub") or "")).strip()
    if not email:
        raise HTTPException(status_code=401, detail="No se encontró email del usuario autenticado")

    try:
        return requisiciones_pendientes_almacen(db, email)
    except ProgrammingError as e:
        msg = str(getattr(e, "orig", e))
        if "Usuario no autorizado" in msg or "no es Empleado de Almacén" in msg:
            raise HTTPException(status_code=401, detail="Usuario no autorizado: no es Empleado de Almacén")
        raise HTTPException(status_code=500, detail="Error al consultar requisiciones pendientes (almacén)")
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Error de base de datos")
    except Exception:
        raise HTTPException(status_code=500, detail="Error inesperado")


# RESPONDER REQUISICION ALMACEN
@router.post(
    "/responder/almacen",
    summary="Empleado de Almacén responde (aprobar/rechazar) una requisición",
    response_model=ResponderRequisicionOut,
)
async def api_responder_requisicion_almacen(
    body: ResponderRequisicionGerenteIn,  # reutiliza el esquema del gerente
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    email = (str(current_user.get("email") or current_user.get("sub") or "")).strip()
    if not email:
        raise HTTPException(status_code=401, detail="No se encontró email del usuario autenticado")

    try:
        return responder_requisicion_almacen(db, body, email)
    except ProgrammingError as e:
        msg = str(getattr(e, "orig", e))
        if "Usuario no autorizado" in msg or "no es Empleado de Almacén" in msg:
            raise HTTPException(status_code=401, detail="Usuario no autorizado: no es Empleado de Almacén")
        if "Estado inválido" in msg or "Comentario es obligatorio" in msg or "no puede aumentar la cantidad" in msg:
            raise HTTPException(status_code=400, detail=msg)
        raise HTTPException(status_code=500, detail="Error al responder la requisición (almacén)")
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Error de base de datos")
    except Exception:
        raise HTTPException(status_code=500, detail="Error inesperado")