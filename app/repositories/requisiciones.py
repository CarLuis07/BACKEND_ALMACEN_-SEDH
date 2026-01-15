from typing import Dict, Any, List
from decimal import Decimal
from sqlalchemy import text, bindparam
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import JSON as PGJSON
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.types import Integer as SAInteger, Numeric as SANumeric, String
from app.schemas.requisiciones.schemas import CrearRequisicionIn, CrearRequisicionOut, RequisicionPendienteOut
from app.schemas.requisiciones.schemas import ResponderRequisicionIn, ResponderRequisicionOut
from app.schemas.requisiciones.schemas import RequisicionPendienteGerenteOut
from app.schemas.requisiciones.schemas import ResponderRequisicionGerenteIn
import json
import logging

logger = logging.getLogger(__name__)


def obtener_usuarios_por_rol(db: Session, nombre_rol: str) -> list[tuple[str, str]]:
    """Obtiene lista de (email, nombre) de usuarios con un rol específico"""
    try:
        query = text("""
            SELECT DISTINCT e.emailinstitucional, e.nombre
            FROM usuarios.empleados e
            JOIN acceso.empleados_roles er ON er.emailinstitucional = e.emailinstitucional
            JOIN acceso.roles r ON r.idrol = er.idrol
            WHERE r.nomrol = :rol AND er.actlaboralmente = TRUE
        """)
        rows = db.execute(query, {"rol": nombre_rol}).fetchall()
        return [(row.emailinstitucional, row.nombre) for row in rows]
    except Exception as e:
        print(f"Error obteniendo usuarios por rol {nombre_rol}: {e}")
        return []


def enviar_notificacion_aprobacion(
    db: Session,
    id_requisicion: str,
    estado: str,
    email_aprobador: str,
    nombre_aprobador: str,
    rol_aprobador: str,
    comentario: str = None
):
    """Envía notificación al solicitante cuando su requisición es aprobada/rechazada"""
    try:
        # Obtener código de requisición y email del solicitante
        query = text("""
            SELECT 
                r.codrequisicion, 
                r.nomempleado, 
                COALESCE(r.creadopor, e.emailinstitucional) AS email_solicitante
            FROM requisiciones.requisiciones r
            LEFT JOIN usuarios.empleados e ON e.emailinstitucional = r.creadopor
            WHERE r.idrequisicion = :id
        """)
        row = db.execute(query, {"id": id_requisicion}).fetchone()
        
        if not row:
            return
            
        cod_req = row.codrequisicion
        nombre_solicitante = row.nomempleado
        email_solicitante = row.email_solicitante
        
        # Determinar mensaje según estado
        if estado.lower() in ['aprobada', 'aprobado']:
            icono = "✅"
            accion = "aprobó"
            tipo_notif = "requisicion_aprobada"
        elif estado.lower() in ['rechazada', 'rechazado']:
            icono = "❌"
            accion = "rechazó"
            tipo_notif = "requisicion_rechazada"
        else:
            icono = "📝"
            accion = "procesó"
            tipo_notif = "requisicion_actualizada"
        
        # Construir mensaje con nombre del aprobador y su rol
        mensaje = f"{icono} {nombre_aprobador} ({rol_aprobador}) {accion} tu requisición {cod_req}"
        if comentario:
            mensaje += f" - Comentario: {comentario}"
        
        # Insertar notificación
        db.execute(
            text("""
                INSERT INTO requisiciones.notificaciones 
                (emailusuario, tipo, mensaje, idrequisicion, leida, fechacreacion)
                VALUES (:email, :tipo, :mensaje, :idrequisicion, FALSE, CURRENT_TIMESTAMP)
            """),
            {
                "email": email_solicitante,
                "tipo": tipo_notif,
                "mensaje": mensaje,
                "idrequisicion": id_requisicion,
            }
        )
        db.commit()
        print(f"✅ Notificación enviada a {email_solicitante}: {mensaje}")
        
    except Exception as e:
        print(f"⚠️ Error al enviar notificación de aprobación: {e}")
        try:
            db.rollback()
        except:
            pass

SQL_CREAR_REQUISICION = """
SELECT requisiciones.crear_requisicion(
    :p_email,
    :p_proIntermedio,
    :p_proFinal,
    :p_obsEmpleado,
    :p_gasTotalPedido,
    :p_json_productos
) AS resultado
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
    :p_comentario,
    CAST(:p_productos AS jsonb)
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
    CAST(:p_productos AS jsonb)
) AS mensaje
"""

SQL_REQUISICIONES_PENDIENTES_ALMACEN = """
SELECT *
FROM requisiciones.requisiciones_pendientes_almacen(:p_email)
"""

SQL_RESPONDER_REQUISICION_ALMACEN = """
SELECT requisiciones.responder_requisicion_almacen(
    :p_id_requisicion,
    :p_email_almacen,
    :p_estado_aprob,
    :p_comentario,
    CAST(:p_productos AS jsonb)
) AS mensaje
"""

def _json_num(v: Decimal | int | float | None) -> float | None:
    return None if v is None else float(v)

def crear_requisicion(db: Session, payload: CrearRequisicionIn) -> CrearRequisicionOut:
    if not payload.email:
        raise ValueError("Email no proporcionado")

    
    productos_json: List[Dict[str, Any]] = [
        {
            "idProducto": str(p.idProducto),
            "nombre": p.nombre or "",
            "cantidad": _json_num(p.cantidad),
            "gasUnitario": _json_num(p.gasUnitario),
            "gasTotalProducto": _json_num(p.gasTotalProducto or (p.cantidad * p.gasUnitario)),
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

    # La función SQL devuelve solo el UUID (resultado)
    id_requisicion = row["resultado"]
    
    # Obtener el código de requisición que se generó automáticamente
    query = text("SELECT codrequisicion FROM requisiciones.requisiciones WHERE idrequisicion = :id")
    req_detail = db.execute(query, {"id": id_requisicion}).first()
    cod_requisicion = req_detail[0] if req_detail else "DESCONOCIDO"
    
    return CrearRequisicionOut(
        idrequisicion=id_requisicion,
        codrequisicion=cod_requisicion,
        nombrejefeInmediato="Pendiente de aprobación",
        emailjefeInmediato="sistema@sedh.gob.hn"
    )

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

        # Excluir requisiciones ya atendidas por Almacén
        try:
            id_req = _first(d, "idRequisicion", "idrequisicion", "id_requisicion")
            if id_req:
                from app.models.requisiciones.requisicion import Requisicion
                req_obj = db.query(Requisicion).filter(Requisicion.IdRequisicion == id_req).first()
                if req_obj:
                    # Si ya tiene timestamp de aprobación en Almacén, no debe aparecer en pendientes
                    if getattr(req_obj, "FechaHoraAprobacionAlmacen", None):
                        continue
                    # Si el estado general indica que no está en espera/pending para Almacén, omitir
                    if req_obj.EstGeneral and req_obj.EstGeneral.upper() not in [
                        "EN ESPERA", "PENDIENTE", "PENDIENTE ALMACEN", "ESPERA ALMACEN"
                    ]:
                        continue
        except Exception:
            # Si falla la verificación, continuar sin filtrar para no romper flujo
            pass

        productos_raw = _first(d, "productos", "Porductos", "porductos")
        productos_list = _parse_productos(productos_raw)
        productos_out = [_map_producto_item(it) for it in productos_list]

        # Intentar múltiples variaciones para el nombre del subordinado/solicitante
        nombre_subordinado = _first(d, "nombreSubordinado", "nombresubordinado", "nombre_subordinado", 
                                    "nomempleado", "NomEmpleado", "nombre_empleado", "solicitante",
                                    "nombreSolicitante", "nombre_solicitante")
        
        # Si no se encontró el nombre, intentar obtenerlo desde la tabla de requisiciones
        if not nombre_subordinado:
            id_requisicion = _first(d, "idRequisicion", "idrequisicion", "id_requisicion")
            if id_requisicion:
                try:
                    from app.models.requisiciones.requisicion import Requisicion
                    req_obj = db.query(Requisicion).filter(Requisicion.IdRequisicion == id_requisicion).first()
                    if req_obj and req_obj.NomEmpleado:
                        nombre_subordinado = req_obj.NomEmpleado
                except Exception as e:
                    print(f"⚠️  No se pudo obtener el nombre del empleado desde la tabla: {e}")
                    nombre_subordinado = "No especificado"

        mapeado: Dict[str, Any] = {
            "idRequisicion": _first(d, "idRequisicion", "idrequisicion", "id_requisicion"),
            "codRequisicion": _first(d, "codRequisicion", "codrequisicion", "cod_requisicion"),
            "nombreSubordinado": nombre_subordinado or "No especificado",
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

    # Convertir productos a JSON si se proporcionan
    productos_json = None
    if payload.productos:
        import json
        productos_json = json.dumps([{"idProducto": str(p.idProducto), "cantidad": float(p.cantidad)} for p in payload.productos])

    params = {
        "p_id_requisicion": payload.idRequisicion,
        "p_email_jefe": email_jefe,
        "p_estado_aprob": payload.estado,
        "p_comentario": payload.comentario,
        "p_productos": productos_json,
    }

    stmt = text(SQL_RESPONDER_REQUISICION_JEFE).bindparams(
        bindparam("p_id_requisicion", type_=PGUUID),
        bindparam("p_email_jefe"),
        bindparam("p_estado_aprob"),
        bindparam("p_comentario"),
        bindparam("p_productos"),
    )

    try:
        row = db.execute(stmt, params).mappings().one()
        
        # Obtener nombre del jefe y código de requisición ANTES del commit
        query_jefe = text("""
            SELECT nombre FROM usuarios.empleados WHERE emailinstitucional = :email
        """)
        row_jefe = db.execute(query_jefe, {"email": email_jefe}).fetchone()
        nombre_jefe = row_jefe.nombre if row_jefe else email_jefe
        
        # Obtener código de requisición
        query_req = text("SELECT codrequisicion FROM requisiciones.requisiciones WHERE idrequisicion = CAST(:id AS UUID)")
        cod_req_result = db.execute(query_req, {"id": str(payload.idRequisicion)}).fetchone()
        cod_req = cod_req_result[0] if cod_req_result else None
        
        # Enviar notificación al solicitante
        enviar_notificacion_aprobacion(
            db=db,
            id_requisicion=str(payload.idRequisicion),
            estado=payload.estado,
            email_aprobador=email_jefe,
            nombre_aprobador=nombre_jefe,
            rol_aprobador="Jefe Inmediato",
            comentario=payload.comentario
        )
        
        # Si aprobó, notificar al siguiente rol (Gerente Administrativo)
        if payload.estado.lower() in ['aprobada', 'aprobado']:
            gerentes = obtener_usuarios_por_rol(db, "GerAdmon")
            for email_ger, nombre_ger in gerentes:
                msg_ger = f"📋 Requisición {cod_req or ''} aprobada por Jefe Inmediato, pendiente tu revisión"
                db.execute(
                    text("""
                        INSERT INTO requisiciones.notificaciones 
                        (emailusuario, tipo, mensaje, idrequisicion, leida, fechacreacion)
                        VALUES (:email, :tipo, :mensaje, :idrequisicion, FALSE, CURRENT_TIMESTAMP)
                    """),
                    {
                        "email": email_ger,
                        "tipo": "requisicion_pendiente",
                        "mensaje": msg_ger,
                        "idrequisicion": str(payload.idRequisicion),
                    }
                )
        
        # Commit al final de todo
        db.commit()
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error en responder_requisicion_jefe: {e}")
        import traceback
        traceback.print_exc()
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
            "nueva_cantidad": _json_num(p.nuevaCantidad if hasattr(p, "nuevaCantidad") else None) or _json_num(getattr(p, "cantidad", None)),
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
        
        # Obtener nombre del gerente y código de requisición ANTES del commit
        query_gerente = text("""
            SELECT nombre FROM usuarios.empleados WHERE emailinstitucional = :email
        """)
        row_gerente = db.execute(query_gerente, {"email": email_gerente}).fetchone()
        nombre_gerente = row_gerente.nombre if row_gerente else email_gerente
        
        # Obtener código de requisición
        query_req = text("SELECT codrequisicion FROM requisiciones.requisiciones WHERE idrequisicion = CAST(:id AS UUID)")
        cod_req_result = db.execute(query_req, {"id": str(payload.idRequisicion)}).fetchone()
        cod_req = cod_req_result[0] if cod_req_result else None
        
        # Enviar notificación al solicitante
        enviar_notificacion_aprobacion(
            db=db,
            id_requisicion=str(payload.idRequisicion),
            estado=payload.estado,
            email_aprobador=email_gerente,
            nombre_aprobador=nombre_gerente,
            rol_aprobador="Gerente Administrativo",
            comentario=payload.comentario
        )
        
        # Si aprobó, notificar al siguiente rol (Jefe de Materiales)
        if payload.estado.lower() in ['aprobada', 'aprobado']:
            jefes_mat = obtener_usuarios_por_rol(db, "JefSerMat")
            for email_jm, nombre_jm in jefes_mat:
                msg_jm = f"📋 Requisición {cod_req or ''} aprobada por Gerente Administrativo, pendiente tu revisión"
                db.execute(
                    text("""
                        INSERT INTO requisiciones.notificaciones 
                        (emailusuario, tipo, mensaje, idrequisicion, leida, fechacreacion)
                        VALUES (:email, :tipo, :mensaje, :idrequisicion, FALSE, CURRENT_TIMESTAMP)
                    """),
                    {
                        "email": email_jm,
                        "tipo": "requisicion_pendiente",
                        "mensaje": msg_jm,
                        "idrequisicion": str(payload.idRequisicion),
                    }
                )
        
        # Commit al final de todo
        db.commit()
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error en responder_requisicion_gerente: {e}")
        import traceback
        traceback.print_exc()
        raise

    return ResponderRequisicionOut(mensaje=row["mensaje"])

# JEFE MATERIALES

def requisiciones_pendientes_jefe_materiales(db: Session, email: str) -> List[RequisicionPendienteGerenteOut]:
    if not email:
        raise ValueError("Email no proporcionado")

    stmt = text(SQL_REQUISICIONES_PENDIENTES_JEFE_MATERIALES).bindparams(
        bindparam("p_email"),
    )
    
    # Ejecutar en una transacción limpia
    try:
        rows = db.execute(stmt, {"p_email": email}).mappings().all()
        db.commit()  # Confirmar transacción de lectura
    except Exception as e:
        db.rollback()
        raise

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

        # Intentar múltiples variaciones para el nombre del empleado/solicitante
        nombre_empleado = _first(d, "nombreEmpleado", "nombreempleado", "nomempleado", "nom_empleado",
                                 "NomEmpleado", "nombre_empleado", "solicitante", 
                                 "nombreSolicitante", "nombre_solicitante", "nombreSubordinado")
        
        # Si no se encontró el nombre, intentar obtenerlo desde la tabla de requisiciones
        if not nombre_empleado:
            id_requisicion = _first(d, "idRequisicion", "idrequisicion", "id_requisicion")
            if id_requisicion:
                try:
                    from app.models.requisiciones.requisicion import Requisicion
                    req_obj = db.query(Requisicion).filter(Requisicion.IdRequisicion == id_requisicion).first()
                    if req_obj and req_obj.NomEmpleado:
                        nombre_empleado = req_obj.NomEmpleado
                except Exception as e:
                    print(f"⚠️  No se pudo obtener el nombre del empleado desde la tabla: {e}")
                    nombre_empleado = "No especificado"

        mapeado = {
            "idRequisicion": _first(d, "idRequisicion", "idrequisicion"),
            "codRequisicion": _first(d, "codRequisicion", "codrequisicion"),
            "nombreEmpleado": nombre_empleado or "No especificado",
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
            "nueva_cantidad": _json_num(p.nuevaCantidad if hasattr(p, "nuevaCantidad") else None) or _json_num(getattr(p, "cantidad", None)),
        }
        for p in payload.productos
    ]
    
    # DEBUG: Log productos JSON
    logger.warning(f"[JefSerMat] productos_json: {json.dumps(productos_json, default=str)}")

    # Guardar historial de cambios de cantidad ANTES de actualizar
    cambios_cantidad = []
    for p in payload.productos:
        cant_original = _json_num(p.cantidadSolicitada if hasattr(p, "cantidadSolicitada") else getattr(p, "cantidad", None))
        cant_nueva = _json_num(p.nuevaCantidad if hasattr(p, "nuevaCantidad") else getattr(p, "cantidad", None))
        
        if cant_original != cant_nueva:
            cambios_cantidad.append({
                "idProducto": str(p.idProducto),
                "cantidadOriginal": cant_original,
                "cantidadNueva": cant_nueva
            })

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
        bindparam("p_productos", type_=PGJSON),  # Será convertido a JSONB por PostgreSQL
    )
    
    logger.warning(f"[JefSerMat] *** ANTES de ejecutar SQL ***")
    logger.warning(f"[JefSerMat] SQL_TEXT: {SQL_RESPONDER_REQUISICION_JEFE_MATERIALES}")
    logger.warning(f"[JefSerMat] PARAMS: {params}")

    try:
        logger.warning(f"[JefSerMat] *** EJECUTANDO SQL ***")
        row = db.execute(stmt, params).mappings().one()
        logger.warning(f"[JefSerMat] *** DESPUÉS de ejecutar SQL - ROW recibido ***")
        logger.warning(f"[JefSerMat] ROW content: {dict(row) if row else 'NULL'}")
        
        resultado = row.mensaje if row and hasattr(row, 'mensaje') else str(row)
        logger.warning(f"[JefSerMat] Resultado SQL: {resultado}")
        
        # Verificar si la función devolvió un error
        if resultado.startswith('ERROR:'):
            logger.error(f"[JefSerMat] Error de función SQL: {resultado}")
            raise ValueError(resultado)

        # *** COMMIT INMEDIATO para asegurar que el INSERT de aprobación se persista ***
        logger.warning(f"[JefSerMat] *** COMMIT INMEDIATO POST-FUNCIÓN SQL ***")
        db.commit()
        logger.warning(f"[JefSerMat] *** COMMIT EXITOSO - Aprobación JefSerMat persistida ***")

        # Obtener nombre del jefe de materiales y código ANTES del commit
        query_jefe = text("""
            SELECT nombre FROM usuarios.empleados WHERE emailinstitucional = :email
        """)
        row_jefe = db.execute(query_jefe, {"email": email_jefe}).fetchone()
        nombre_jefe = row_jefe.nombre if row_jefe else email_jefe
        # Obtener código de requisición
        query_req = text("SELECT codrequisicion FROM requisiciones.requisiciones WHERE idrequisicion = CAST(:id AS UUID)")
        cod_req_result = db.execute(query_req, {"id": str(payload.idRequisicion)}).fetchone()
        cod_req = cod_req_result[0] if cod_req_result else None
        
        # Registrar cambios de cantidad en auditoría
        if cambios_cantidad and payload.estado.upper() in ['APROBADO', 'APROBADA']:
            observaciones_cambios = "Cambios de cantidad: " + "; ".join([
                f"Producto {c['idProducto']}: {c['cantidadOriginal']} → {c['cantidadNueva']}"
                for c in cambios_cantidad
            ])
            registrar_auditoria_requisicion(
                db=db,
                id_requisicion=str(payload.idRequisicion),
                tipo_accion="CAMBIO_CANTIDAD_JEFE_MATERIALES",
                id_usuario_accion="",  # Se obtiene del token en el router
                nombre_usuario_accion=nombre_jefe,
                descripcion_accion="Cambio de cantidades por Jefe de Materiales",
                observaciones=observaciones_cambios
            )
        
        # Enviar notificación al solicitante
        enviar_notificacion_aprobacion(
            db=db,
            id_requisicion=str(payload.idRequisicion),
            estado=payload.estado,
            email_aprobador=email_jefe,
            nombre_aprobador=nombre_jefe,
            rol_aprobador="Jefe de Materiales",
            comentario=payload.comentario
        )
        
        # Si aprobó, notificar al siguiente rol (Empleado de Almacén)
        if payload.estado.lower() in ['aprobada', 'aprobado']:
            empleados_alm = obtener_usuarios_por_rol(db, "EmpAlmacen")
            for email_alm, nombre_alm in empleados_alm:
                msg_alm = f"📦 Requisición {cod_req or ''} aprobada por Jefe de Materiales, lista para despacho"
                db.execute(
                    text("""
                        INSERT INTO requisiciones.notificaciones 
                        (emailusuario, tipo, mensaje, idrequisicion, leida, fechacreacion)
                        VALUES (:email, :tipo, :mensaje, :idrequisicion, FALSE, CURRENT_TIMESTAMP)
                    """),
                    {
                        "email": email_alm,
                        "tipo": "requisicion_pendiente",
                        "mensaje": msg_alm,
                        "idrequisicion": str(payload.idRequisicion),
                    }
                )

            # Registrar estado PENDIENTE para el rol EmpAlmacen en la tabla de Aprobaciones
            try:
                estado_actual_alm = db.execute(
                    text(
                        """
                        SELECT estadoaprobacion 
                        FROM requisiciones.aprobaciones 
                        WHERE idrequisicion = CAST(:id AS UUID) AND rol = 'EmpAlmacen' 
                        ORDER BY fecaprobacion DESC NULLS LAST 
                        LIMIT 1
                        """
                    ),
                    {"id": str(payload.idRequisicion)}
                ).fetchone()

                if not estado_actual_alm or (str(estado_actual_alm[0] or '').upper() != 'PENDIENTE'):
                    db.execute(
                        text(
                            """
                            INSERT INTO requisiciones.aprobaciones 
                            (idrequisicion, emailinstitucional, rol, estadoaprobacion, comentario, fecaprobacion)
                            VALUES (CAST(:id AS UUID), NULL, 'EmpAlmacen', 'Pendiente', NULL, NULL)
                            """
                        ),
                        {"id": str(payload.idRequisicion)}
                    )
            except Exception as ap_e:
                print(f"⚠️  No se pudo registrar estado pendiente para EmpAlmacen: {ap_e}")

        # Commit de auditoría y notificaciones
        try:
            db.commit()
            logger.warning(f"[JefSerMat] *** COMMIT final (auditoría/notificaciones) exitoso ***")
        except Exception as commit_e:
            logger.error(f"[JefSerMat] Error en commit final: {commit_e}")
            # No hacer rollback aquí porque la aprobación ya está commiteada

    except Exception as e:
        logger.error(f"[JefSerMat] *** EXCEPCIÓN en función: {e} ***")
        db.rollback()
        print(f"❌ Error en responder_requisicion_jefe_materiales: {e}")
        import traceback
        traceback.print_exc()
        raise

    logger.warning(f"[JefSerMat] *** RETORNANDO RESULTADO: {row['mensaje']} ***")
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



def responder_requisicion_almacen(
    db: Session,
    payload: ResponderRequisicionGerenteIn,
    email_almacen: str
) -> ResponderRequisicionOut:
    if not email_almacen:
        raise ValueError("Email no proporcionado")

    # Convertir productos al formato esperado por la función SQL
    productos_json: List[Dict[str, Any]] = [
        {
            "idProducto": str(p.idProducto),
            "nuevaCantidad": float(p.nuevaCantidad if hasattr(p, "nuevaCantidad") and p.nuevaCantidad is not None else getattr(p, "cantidad", 0)),
        }
        for p in payload.productos
    ]

    params = {
        "p_id_requisicion": payload.idRequisicion,
        "p_email_almacen": email_almacen,
        "p_estado_aprob": payload.estado,
        "p_comentario": payload.comentario or "",
        "p_productos": json.dumps(productos_json),
    }

    stmt = text(SQL_RESPONDER_REQUISICION_ALMACEN).bindparams(
        bindparam("p_id_requisicion", type_=PGUUID),
        bindparam("p_email_almacen"),
        bindparam("p_estado_aprob"),
        bindparam("p_comentario"),
        bindparam("p_productos"),
    )

    try:
        row = db.execute(stmt, params).mappings().one()
        
        # Obtener nombre del encargado de almacén ANTES del commit
        query_almacen = text("""
            SELECT nombre FROM usuarios.empleados WHERE emailinstitucional = :email
        """)
        row_almacen = db.execute(query_almacen, {"email": email_almacen}).fetchone()
        nombre_almacen = row_almacen.nombre if row_almacen else email_almacen
        
        # Enviar notificación al solicitante
        enviar_notificacion_aprobacion(
            db=db,
            id_requisicion=str(payload.idRequisicion),
            estado=payload.estado,
            email_aprobador=email_almacen,
            nombre_aprobador=nombre_almacen,
            rol_aprobador="Encargado de Almacén",
            comentario=payload.comentario
        )
        
        # Commit al final
        db.commit()
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error en responder_requisicion_almacen: {e}")
        import traceback
        traceback.print_exc()
        raise


# ===== FUNCIONES DE AUDITORÍA Y TIMESTAMPS =====

def registrar_auditoria_requisicion(
    db: Session,
    id_requisicion: str,
    tipo_accion: str,
    id_usuario_accion: str,
    nombre_usuario_accion: str,
    descripcion_accion: str = None,
    observaciones: str = None
) -> bool:
    """
    Registra una acción en la auditoría de requisiciones
    
    Args:
        db: Session de la base de datos
        id_requisicion: ID de la requisición
        tipo_accion: CREADA, ENVIADA, APROBADA_JEFE, APROBADA_ALMACEN, RECHAZADA, ENTREGADA
        id_usuario_accion: ID del usuario que realizó la acción
        nombre_usuario_accion: Nombre del usuario que realizó la acción
        descripcion_accion: Descripción opcional de la acción
        observaciones: Observaciones opcionales
    
    Returns:
        True si se registró correctamente, False si hubo error
    """
    try:
        from datetime import datetime
        
        query = text("""
            INSERT INTO requisiciones.auditoria_requisiciones 
            (id_requisicion, tipo_accion, id_usuario_accion, nombre_usuario_accion, 
             descripcion_accion, fecha_hora_accion, observaciones)
            VALUES (:id_req, :tipo_acc, :id_usr, :nom_usr, :desc_acc, CURRENT_TIMESTAMP, :obs)
            RETURNING id_auditoria
        """)
        
        params = {
            "id_req": id_requisicion,
            "tipo_acc": tipo_accion,
            "id_usr": id_usuario_accion,
            "nom_usr": nombre_usuario_accion,
            "desc_acc": descripcion_accion,
            "obs": observaciones
        }
        
        result = db.execute(query, params).scalar()
        db.commit()
        return result is not None
    except Exception as e:
        print(f"Error registrando auditoría: {e}")
        db.rollback()
        return False


def obtener_timeline_requisicion(db: Session, id_requisicion: str) -> list[Dict[str, Any]]:
    """
    Obtiene el timeline completo de una requisición con todos los eventos
    
    Returns:
        Lista de eventos ordenados cronológicamente
    """
    try:
        query = text("""
            SELECT 
                id_auditoria,
                tipo_accion,
                fecha_hora_accion AT TIME ZONE 'America/Tegucigalpa' AS fecha_hora_accion,
                nombre_usuario_accion,
                descripcion_accion,
                observaciones
            FROM requisiciones.auditoria_requisiciones
            WHERE id_requisicion = :id_req
            ORDER BY fecha_hora_accion ASC
        """)
        
        rows = db.execute(query, {"id_req": id_requisicion}).mappings().fetchall()
        
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"Error obteniendo timeline: {e}")
        return []


def obtener_tiempos_requisicion(db: Session, id_requisicion: str) -> Dict[str, Any]:
    """
    Calcula los tiempos transcurridos entre cada etapa
    
    Returns:
        Diccionario con información de tiempos
    """
    try:
        query = text("""
            SELECT 
                idrequisicion AS id_requisicion,
                codrequisicion AS codigo,
                nomempleado AS empleado,
                fecha_hora_creacion AS fecha_creacion,
                fecha_hora_envio AS fecha_envio,
                fecha_hora_aprobacion_jefe AS fecha_aprobacion_jefe,
                fecha_hora_aprobacion_almacen AS fecha_aprobacion_almacen,
                fecha_hora_entrega AS fecha_entrega,
                EXTRACT(EPOCH FROM (fecha_hora_envio - fecha_hora_creacion))/3600 AS horas_creacion_a_envio,
                EXTRACT(EPOCH FROM (fecha_hora_aprobacion_jefe - fecha_hora_envio))/3600 AS horas_envio_a_jefe,
                EXTRACT(EPOCH FROM (fecha_hora_aprobacion_almacen - fecha_hora_aprobacion_jefe))/3600 AS horas_jefe_a_almacen,
                EXTRACT(EPOCH FROM (fecha_hora_entrega - fecha_hora_aprobacion_almacen))/3600 AS horas_almacen_a_entrega,
                EXTRACT(EPOCH FROM (COALESCE(fecha_hora_entrega, CURRENT_TIMESTAMP) - fecha_hora_creacion))/24 AS dias_totales
            FROM requisiciones.requisiciones
            WHERE idrequisicion = :id_req
        """)
        
        row = db.execute(query, {"id_req": id_requisicion}).mappings().first()
        
        return dict(row) if row else {}
    except Exception as e:
        print(f"Error obteniendo tiempos: {e}")
        return {}


def actualizar_timestamp_envio(db: Session, id_requisicion: str, id_usuario: str) -> bool:
    """Actualiza el timestamp cuando se envía la requisición"""
    try:
        query = text("""
            UPDATE requisiciones.requisiciones
            SET fecha_hora_envio = CURRENT_TIMESTAMP,
                id_empleado_creador = :id_usuario
            WHERE idrequisicion = CAST(:id_req AS UUID)
        """)
        
        result = db.execute(query, {"id_req": str(id_requisicion), "id_usuario": str(id_usuario)})
        db.commit()
        print(f"✅ Timestamp envío actualizado. Filas afectadas: {result.rowcount}")
        return True
    except Exception as e:
        print(f"❌ Error actualizando timestamp envío: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False


def actualizar_timestamp_aprobacion_jefe(db: Session, id_requisicion: str, id_jefe: str) -> bool:
    """Actualiza el timestamp cuando el jefe aprueba"""
    try:
        query = text("""
            UPDATE requisiciones.requisiciones
            SET fecha_hora_aprobacion_jefe = CURRENT_TIMESTAMP,
                id_jefe_aprobador = :id_jefe
            WHERE idrequisicion = CAST(:id_req AS UUID)
        """)
        
        result = db.execute(query, {"id_req": str(id_requisicion), "id_jefe": str(id_jefe)})
        db.commit()
        print(f"✅ Timestamp aprobación jefe actualizado. Filas afectadas: {result.rowcount}")
        return True
    except Exception as e:
        print(f"❌ Error actualizando timestamp aprobación jefe: {e}")
        db.rollback()
        return False


def actualizar_timestamp_aprobacion_almacen(db: Session, id_requisicion: str, id_almacen: str) -> bool:
    """Actualiza el timestamp cuando almacén aprueba"""
    try:
        # Solo actualizar si tenemos un ID válido
        if not id_almacen or id_almacen == "":
            print(f"⚠️  Sin ID de almacén, saltando actualización de timestamp")
            return True
        
        query = text("""
            UPDATE requisiciones.requisiciones
            SET fecha_hora_aprobacion_almacen = CURRENT_TIMESTAMP,
                id_almacen_aprobador = :id_almacen
            WHERE idrequisicion = CAST(:id_req AS UUID)
        """)
        
        result = db.execute(query, {"id_req": str(id_requisicion), "id_almacen": str(id_almacen)})
        db.commit()
        print(f"✅ Timestamp aprobación almacén actualizado. Filas afectadas: {result.rowcount}")
        return True
    except Exception as e:
        print(f"❌ Error actualizando timestamp aprobación almacén: {e}")
        db.rollback()
        return False


def actualizar_timestamp_entrega(db: Session, id_requisicion: str, entregado_por: str, recibido_por: str) -> bool:
    """Actualiza el timestamp cuando se entrega la requisición"""
    try:
        query = text("""
            UPDATE requisiciones.requisiciones
            SET fecha_hora_entrega = CURRENT_TIMESTAMP,
                reqentregadopor = :entregado_por,
                reqrecibidopor = :recibido_por
            WHERE idrequisicion = :id_req
        """)
        
        db.execute(query, {
            "id_req": id_requisicion,
            "entregado_por": entregado_por,
            "recibido_por": recibido_por
        })
        db.commit()
        return True
    except Exception as e:
        print(f"Error actualizando timestamp entrega: {e}")
        db.rollback()
        return False


def actualizar_timestamp_rechazo(db: Session, id_requisicion: str) -> bool:
    """Actualiza el timestamp cuando se rechaza la requisición"""
    try:
        query = text("""
            UPDATE requisiciones.requisiciones
            SET fecha_hora_rechazo = CURRENT_TIMESTAMP
            WHERE idrequisicion = CAST(:id_req AS UUID)
        """)
        
        result = db.execute(query, {"id_req": str(id_requisicion)})
        db.commit()
        print(f"✅ Timestamp rechazo actualizado. Filas afectadas: {result.rowcount}")
        return True
    except Exception as e:
        print(f"❌ Error actualizando timestamp rechazo: {e}")
        db.rollback()
        return False
        raise

    return ResponderRequisicionOut(mensaje=row["mensaje"])