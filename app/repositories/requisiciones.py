from typing import Dict, Any, List
from decimal import Decimal
from sqlalchemy import text, bindparam
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import JSON as PGJSON
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.types import Integer as SAInteger, Numeric as SANumeric
from app.schemas.requisiciones.schemas import CrearRequisicionIn, CrearRequisicionOut, RequisicionPendienteOut
from app.schemas.requisiciones.schemas import ResponderRequisicionIn, ResponderRequisicionOut
from app.schemas.requisiciones.schemas import RequisicionPendienteGerenteOut
from app.schemas.requisiciones.schemas import ResponderRequisicionGerenteIn, ResponderRequisicionOut
import json

SQL_CREAR_REQUISICION = """
SELECT requisiciones.crear_requisicion(
    :p_email,
    :p_proIntermedio,
    :p_proFinal,
    :p_obsEmpleado,
    :p_gasTotalPedido,
    :p_json_productos
) AS idrequisicion
"""

SQL_REQUISICIONES_PENDIENTES_JEFE = """
SELECT *
FROM requisiciones.requisiciones_pendientes_jefe(:p_email)
"""

SQL_REQUISICIONES_PENDIENTES_JEFE_MATERIALES = """
SELECT *
FROM requisiciones.requisiciones_pendientes_jefe_materiales(:p_email)
"""

SQL_REQUISICIONES_PENDIENTES_GERENTE = """
SELECT *
FROM requisiciones.requisiciones_pendientes_gerente(:p_email)
"""

SQL_RESPONDER_REQUISICION_JEFE = """
SELECT requisiciones.responder_requisicion_jefe(
    :p_id_requisicion,
    :p_email_jefe,
    :p_estado_aprob,
    :p_comentario
) AS mensaje
"""

SQL_RESPONDER_REQUISICION_GERENTE = """
SELECT requisiciones.responder_requisicion_gerente(
    :p_id_requisicion,
    :p_email_gerente,
    :p_estado_aprob,
    :p_comentario,
    :p_productos
) AS mensaje
"""

SQL_RESPONDER_REQUISICION_JEFE_MATERIALES = """
SELECT requisiciones.responder_requisicion_jefe_materiales(
    :p_id_requisicion,
    :p_email_jefe,
    :p_estado_aprob,
    :p_comentario,
    :p_productos
) AS mensaje
"""

SQL_REQUISICIONES_PENDIENTES_ALMACEN = """
SELECT *
FROM requisiciones.requisiciones_pendientes_almacen(:p_email)
"""

def _json_num(v: Decimal | int | float | None) -> float | None:
    return None if v is None else float(v)

def crear_requisicion(db: Session, payload: CrearRequisicionIn) -> CrearRequisicionOut:
    if not payload.email:
        raise ValueError("Email no proporcionado")

    
    productos_json: List[Dict[str, Any]] = [
        {
            "nombre": p.nombre,
            "cantidad": _json_num(p.cantidad),
            "gasUnitario": _json_num(p.gasUnitario),
            "gasTotalProducto": _json_num(p.gasTotalProducto),
        }
        for p in payload.productos
    ]

    
    params: Dict[str, Any] = {
        "p_email": payload.email,                   # TEXT
        "p_proIntermedio": payload.proIntermedio,   # NUMERIC (Decimal)
        "p_proFinal": int(payload.proFinal),        # INTEGER
        "p_obsEmpleado": payload.obsEmpleado,       # TEXT
        "p_gasTotalPedido": payload.gasTotalPedido, # NUMERIC (Decimal)
        "p_json_productos": productos_json,         # JSON nativo
    }

    stmt = text(SQL_CREAR_REQUISICION).bindparams(
        bindparam("p_email"),
        bindparam("p_proIntermedio", type_=SANumeric),
        bindparam("p_proFinal", type_=SAInteger),
        bindparam("p_obsEmpleado"),
        bindparam("p_gasTotalPedido", type_=SANumeric),
        bindparam("p_json_productos", type_=PGJSON),
    )

    try:
        row = db.execute(stmt, params).mappings().one()
        db.commit()
    except Exception:
        db.rollback()
        raise

    return CrearRequisicionOut(idrequisicion=row["idrequisicion"])

def requisiciones_pendientes_jefe(db: Session, email: str) -> List[RequisicionPendienteOut]:
    if not email:
        raise ValueError("Email no proporcionado")

    stmt = text(SQL_REQUISICIONES_PENDIENTES_JEFE).bindparams(
        bindparam("p_email"),
    )

    rows = db.execute(stmt, {"p_email": email}).mappings().all()

    def _first(d: Dict[str, Any], *keys: str) -> Any:
        for k in keys:
            if k in d:
                return d[k]
        return None

    def _parse_productos(raw: Any) -> List[Dict[str, Any]]:
        # Si viene como texto, parsear JSON
        if isinstance(raw, str):
            try:
                return json.loads(raw)
            except Exception:
                try:
                    # fallback por casos con comillas duplicadas en dumps intermedios
                    return json.loads(raw.replace('""', '"'))
                except Exception:
                    return []
        if isinstance(raw, list):
            return raw
        return []

    def _map_producto_item(item: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "idProducto": _first(item, "idProducto", "id_producto"),
            "nombre": _first(item, "nombre", "nombre_producto"),
            "cantidad": _first(item, "cantidad", "cantidad_solicitada"),
            "gasUnitario": _first(item, "gasUnitario", "gas_unitario"),
            "gasTotalProducto": _first(item, "gasTotalProducto", "gas_total_producto"),
        }

    resultados: List[RequisicionPendienteOut] = []
    for r in rows:
        d = dict(r)

        productos_raw = _first(d, "productos", "Porductos", "porductos")
        productos_list = _parse_productos(productos_raw)
        productos_out = [_map_producto_item(it) for it in productos_list]

        mapeado: Dict[str, Any] = {
            "idRequisicion": _first(d, "idRequisicion", "idrequisicion", "id_requisicion"),
            "codRequisicion": _first(d, "codRequisicion", "codrequisicion", "cod_requisicion"),
            "nombreSubordinado": _first(d, "nombreSubordinado", "nombresubordinado", "nombre_subordinado"),
            "dependencia": _first(d, "dependencia"),
            "fecSolicitud": _first(d, "fecSolicitud", "fecsolicitud", "fec_solicitud"),
            "codPrograma": _first(d, "codPrograma", "codprograma", "cod_programa"),
            "proIntermedio": _first(d, "proIntermedio", "prointermedio", "pro_intermedio"),
            "proFinal": _first(d, "proFinal", "profinal", "pro_final"),
            "obsEmpleado": _first(d, "obsEmpleado", "obsempleado", "obs_empleado"),
            "gasTotalDelPedido": _first(d, "gasTotalDelPedido", "gastotaldelpedido", "gas_total_del_pedido"),
            "productos": productos_out,
        }

        resultados.append(RequisicionPendienteOut(**mapeado))

    return resultados



def responder_requisicion_jefe(db: Session, payload: ResponderRequisicionIn, email_jefe: str) -> ResponderRequisicionOut:
    if not email_jefe:
        raise ValueError("Email no proporcionado")

    params = {
        "p_id_requisicion": payload.idRequisicion,
        "p_email_jefe": email_jefe,
        "p_estado_aprob": payload.estado,     # ya viene normalizado a MAYÚSCULAS
        "p_comentario": payload.comentario,
    }

    stmt = text(SQL_RESPONDER_REQUISICION_JEFE).bindparams(
        bindparam("p_id_requisicion", type_=PGUUID),
        bindparam("p_email_jefe"),
        bindparam("p_estado_aprob"),
        bindparam("p_comentario"),
    )

    try:
        row = db.execute(stmt, params).mappings().one()
        db.commit()
    except Exception:
        db.rollback()
        raise

    return ResponderRequisicionOut(mensaje=row["mensaje"])

# GERENTE ADMINISTRATIVO

def requisiciones_pendientes_gerente(db: Session, email: str) -> List[RequisicionPendienteGerenteOut]:
    if not email:
        raise ValueError("Email no proporcionado")

    stmt = text(SQL_REQUISICIONES_PENDIENTES_GERENTE).bindparams(
        bindparam("p_email"),
    )
    rows = db.execute(stmt, {"p_email": email}).mappings().all()

    def _first(d: Dict[str, Any], *keys: str) -> Any:
        for k in keys:
            if k in d:
                return d[k]
        return None

    def _parse_productos(raw: Any) -> List[Dict[str, Any]]:
        if isinstance(raw, str):
            import json
            try:
                return json.loads(raw)
            except Exception:
                try:
                    return json.loads(raw.replace('""', '"'))
                except Exception:
                    return []
        if isinstance(raw, list):
            return raw
        return []

    def _map_producto_item(item: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "idProducto": _first(item, "idProducto", "id_producto"),
            "nombre": _first(item, "nombre", "nombre_producto"),
            "cantidad": _first(item, "cantidad", "cantidad_solicitada"),
            "gasUnitario": _first(item, "gasUnitario", "gas_unitario"),
            "gasTotalProducto": _first(item, "gasTotalProducto", "gas_total_producto"),
        }

    resultados: List[RequisicionPendienteGerenteOut] = []
    for r in rows:
        d = dict(r)
        productos_list = _parse_productos(_first(d, "productos", "Productos"))
        productos_out = [_map_producto_item(it) for it in productos_list]

        mapeado = {
            "idRequisicion": _first(d, "idRequisicion", "idrequisicion"),
            "codRequisicion": _first(d, "codRequisicion", "codrequisicion"),
            "nombreEmpleado": _first(d, "nombreEmpleado", "nombreempleado", "nomempleado", "nom_empleado"),
            "dependencia": _first(d, "dependencia"),
            "fecSolicitud": _first(d, "fecSolicitud", "fecsolicitud"),
            "codPrograma": _first(d, "codPrograma", "codprograma"),
            "proIntermedio": _first(d, "proIntermedio", "prointermedio"),
            "proFinal": _first(d, "proFinal", "profinal"),
            "obsEmpleado": _first(d, "obsEmpleado", "obsempleado"),
            "gasTotalDelPedido": _first(d, "gasTotalDelPedido", "gastotaldelpedido"),
            "productos": productos_out,
        }
        resultados.append(RequisicionPendienteGerenteOut(**mapeado))

    return resultados

def responder_requisicion_gerente(
    db: Session,
    payload: ResponderRequisicionGerenteIn,
    email_gerente: str
) -> ResponderRequisicionOut:
    if not email_gerente:
        raise ValueError("Email no proporcionado")

    productos_json: List[Dict[str, Any]] = [
        {
            "id_producto": str(p.idProducto),
            "nueva_cantidad": _json_num(p.nuevaCantidad),
        }
        for p in payload.productos
    ]

    params = {
        "p_id_requisicion": payload.idRequisicion,
        "p_email_gerente": email_gerente,
        "p_estado_aprob": payload.estado,     # normalizado a MAYÚSCULA
        "p_comentario": payload.comentario,
        "p_productos": productos_json,        # JSON array
    }

    stmt = text(SQL_RESPONDER_REQUISICION_GERENTE).bindparams(
        bindparam("p_id_requisicion", type_=PGUUID),
        bindparam("p_email_gerente"),
        bindparam("p_estado_aprob"),
        bindparam("p_comentario"),
        bindparam("p_productos", type_=PGJSON),
    )

    try:
        row = db.execute(stmt, params).mappings().one()
        db.commit()
    except Exception:
        db.rollback()
        raise

    return ResponderRequisicionOut(mensaje=row["mensaje"])

# JEFE MATERIALES

def requisiciones_pendientes_jefe_materiales(db: Session, email: str) -> List[RequisicionPendienteGerenteOut]:
    if not email:
        raise ValueError("Email no proporcionado")

    stmt = text(SQL_REQUISICIONES_PENDIENTES_JEFE_MATERIALES).bindparams(
        bindparam("p_email"),
    )
    rows = db.execute(stmt, {"p_email": email}).mappings().all()

    def _first(d: Dict[str, Any], *keys: str) -> Any:
        for k in keys:
            if k in d:
                return d[k]
        return None

    def _parse_productos(raw: Any) -> List[Dict[str, Any]]:
        if isinstance(raw, str):
            try:
                return json.loads(raw)
            except Exception:
                try:
                    return json.loads(raw.replace('""', '"'))
                except Exception:
                    return []
        if isinstance(raw, list):
            return raw
        return []

    def _map_producto_item(item: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "idProducto": _first(item, "idProducto", "id_producto"),
            "nombre": _first(item, "nombre", "nombre_producto"),
            "cantidad": _first(item, "cantidad", "cantidad_solicitada"),
            "gasUnitario": _first(item, "gasUnitario", "gas_unitario"),
            "gasTotalProducto": _first(item, "gasTotalProducto", "gas_total_producto"),
        }

    resultados: List[RequisicionPendienteGerenteOut] = []
    for r in rows:
        d = dict(r)
        productos_list = _parse_productos(_first(d, "productos", "Productos"))
        productos_out = [_map_producto_item(it) for it in productos_list]

        mapeado = {
            "idRequisicion": _first(d, "idRequisicion", "idrequisicion"),
            "codRequisicion": _first(d, "codRequisicion", "codrequisicion"),
            "nombreEmpleado": _first(d, "nombreEmpleado", "nombreempleado", "nomempleado", "nom_empleado"),
            "dependencia": _first(d, "dependencia"),
            "fecSolicitud": _first(d, "fecSolicitud", "fecsolicitud"),
            "codPrograma": _first(d, "codPrograma", "codprograma"),
            "proIntermedio": _first(d, "proIntermedio", "prointermedio"),
            "proFinal": _first(d, "proFinal", "profinal"),
            "obsEmpleado": _first(d, "obsEmpleado", "obsempleado"),
            "gasTotalDelPedido": _first(d, "gasTotalDelPedido", "gastotaldelpedido"),
            "productos": productos_out,
        }
        resultados.append(RequisicionPendienteGerenteOut(**mapeado))

    return resultados

def responder_requisicion_jefe_materiales(
    db: Session,
    payload: ResponderRequisicionGerenteIn,
    email_jefe: str
) -> ResponderRequisicionOut:
    if not email_jefe:
        raise ValueError("Email no proporcionado")

    productos_json: List[Dict[str, Any]] = [
        {
            "id_producto": str(p.idProducto),
            "nueva_cantidad": _json_num(p.nuevaCantidad),
        }
        for p in payload.productos
    ]

    params = {
        "p_id_requisicion": payload.idRequisicion,
        "p_email_jefe": email_jefe,
        "p_estado_aprob": payload.estado,     
        "p_comentario": payload.comentario,
        "p_productos": productos_json,        
    }

    stmt = text(SQL_RESPONDER_REQUISICION_JEFE_MATERIALES).bindparams(
        bindparam("p_id_requisicion", type_=PGUUID),
        bindparam("p_email_jefe"),
        bindparam("p_estado_aprob"),
        bindparam("p_comentario"),
        bindparam("p_productos", type_=PGJSON),
    )

    try:
        row = db.execute(stmt, params).mappings().one()
        db.commit()
    except Exception:
        db.rollback()
        raise

    return ResponderRequisicionOut(mensaje=row["mensaje"])

# EMPLEADOS ALMACEN

def requisiciones_pendientes_almacen(db: Session, email: str) -> List[RequisicionPendienteGerenteOut]:
    if not email:
        raise ValueError("Email no proporcionado")

    stmt = text(SQL_REQUISICIONES_PENDIENTES_ALMACEN).bindparams(
        bindparam("p_email"),
    )
    rows = db.execute(stmt, {"p_email": email}).mappings().all()

    def _first(d: Dict[str, Any], *keys: str) -> Any:
        for k in keys:
            if k in d:
                return d[k]
        return None

    def _parse_productos(raw: Any) -> List[Dict[str, Any]]:
        if isinstance(raw, str):
            try:
                return json.loads(raw)
            except Exception:
                try:
                    return json.loads(raw.replace('""', '"'))
                except Exception:
                    return []
        if isinstance(raw, list):
            return raw
        return []

    def _map_producto_item(item: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "idProducto": _first(item, "idProducto", "id_producto"),
            "nombre": _first(item, "nombre", "nombre_producto"),
            "cantidad": _first(item, "cantidad", "cantidad_solicitada"),
            "gasUnitario": _first(item, "gasUnitario", "gas_unitario"),
            "gasTotalProducto": _first(item, "gasTotalProducto", "gas_total_producto"),
        }

    resultados: List[RequisicionPendienteGerenteOut] = []
    for r in rows:
        d = dict(r)
        productos_list = _parse_productos(_first(d, "productos", "Productos"))
        productos_out = [_map_producto_item(it) for it in productos_list]

        mapeado = {
            "idRequisicion": _first(d, "idRequisicion", "idrequisicion"),
            "codRequisicion": _first(d, "codRequisicion", "codrequisicion"),
            "nombreEmpleado": _first(d, "nombreEmpleado", "nombreempleado", "nomempleado", "nom_empleado"),
            "dependencia": _first(d, "dependencia"),
            "fecSolicitud": _first(d, "fecSolicitud", "fecsolicitud"),
            "codPrograma": _first(d, "codPrograma", "codprograma"),
            "proIntermedio": _first(d, "proIntermedio", "prointermedio"),
            "proFinal": _first(d, "proFinal", "profinal"),
            "obsEmpleado": _first(d, "obsEmpleado", "obsempleado"),
            "gasTotalDelPedido": _first(d, "gasTotalDelPedido", "gastotaldelpedido"),
            "productos": productos_out,
        }
        resultados.append(RequisicionPendienteGerenteOut(**mapeado))

    return resultados