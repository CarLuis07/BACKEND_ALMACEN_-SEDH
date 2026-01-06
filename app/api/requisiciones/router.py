from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import ProgrammingError, SQLAlchemyError
from sqlalchemy import text
from io import BytesIO
from io import StringIO
from datetime import datetime, date
import csv
from app.core.database import get_db
from app.core.security import get_current_user

router = APIRouter()


def _iso_with_time(value):
    """Serialize date/datetime to ISO always including a time component to avoid JS TZ shift."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time()).isoformat()
    return str(value)

@router.get("/email-log", summary="Historial de env??os de correo")
async def api_email_log(
    db: Session = Depends(get_db),
    destinatario: str = None,
    idrequisicion: str = None,
    estado: str = None,
    from_: str = None,
    to: str = None,
    q: str = None,
    limit: int = 100,
    offset: int = 0,
):
    """
    Devuelve el historial de env??os de correo. Permite filtrar por destinatario o idrequisicion.
    """
    query = """
        SELECT el.idlog, el.idrequisicion, el.destinatario, el.asunto, el.estado, el.error, el.fecha_envio,
               COALESCE(r.codrequisicion, '') as codrequisicion
        FROM requisiciones.email_log el
        LEFT JOIN requisiciones.requisiciones r ON el.idrequisicion = r.idrequisicion
    """
    filtros = []
    params = {}
    if destinatario:
        filtros.append("el.destinatario = :destinatario")
        params["destinatario"] = destinatario
    if idrequisicion:
        filtros.append("el.idrequisicion = :idrequisicion")
        params["idrequisicion"] = idrequisicion
    if estado:
        filtros.append("el.estado = :estado")
        params["estado"] = estado
    if from_:
        filtros.append("el.fecha_envio::date >= :from")
        params["from"] = from_
    if to:
        filtros.append("el.fecha_envio::date <= :to")
        params["to"] = to
    if q:
        filtros.append("(el.asunto ILIKE :q OR el.cuerpo ILIKE :q)")
        params["q"] = f"%{q}%"
    if filtros:
        query += " WHERE " + " AND ".join(filtros)
    # Validar l??mites
    limit = max(1, min(limit, 500))
    offset = max(0, offset)
    query += " ORDER BY el.fecha_envio DESC LIMIT :limit OFFSET :offset"
    params["limit"] = limit
    params["offset"] = offset
    rows = db.execute(text(query), params).fetchall()
    return [dict(row._mapping) for row in rows]

@router.get("/email-log/count", summary="Total de logs de correo")
async def api_email_log_count(
    db: Session = Depends(get_db),
    destinatario: str = None,
    idrequisicion: str = None,
    estado: str = None,
    from_: str = None,
    to: str = None,
    q: str = None,
):
    """
    Devuelve el total de registros en requisiciones.email_log aplicando los mismos filtros.
    """
    query = "SELECT COUNT(*) AS total FROM requisiciones.email_log"
    filtros = []
    params = {}
    if destinatario:
        filtros.append("destinatario = :destinatario")
        params["destinatario"] = destinatario
    if idrequisicion:
        filtros.append("idrequisicion = :idrequisicion")
        params["idrequisicion"] = idrequisicion
    if estado:
        filtros.append("estado = :estado")
        params["estado"] = estado
    if from_:
        filtros.append("fecha_envio::date >= :from")
        params["from"] = from_
    if to:
        filtros.append("fecha_envio::date <= :to")
        params["to"] = to
    if q:
        filtros.append("(asunto ILIKE :q OR cuerpo ILIKE :q)")
        params["q"] = f"%{q}%"
    if filtros:
        query += " WHERE " + " AND ".join(filtros)
    row = db.execute(text(query), params).fetchone()
    total = int(row.total) if row else 0
    return {"total": total}

@router.get("/email-log/export", summary="Exportar logs de correo en CSV")
async def api_email_log_export(
    db: Session = Depends(get_db),
    destinatario: str = None,
    idrequisicion: str = None,
    estado: str = None,
    from_: str = None,
    to: str = None,
    include_cuerpo: bool = False,
    q: str = None,
):
    """
    Exporta los logs de correo en formato CSV aplicando filtros.
    """
    select_cols = "idlog, fecha_envio, destinatario, asunto, estado, error, idrequisicion"
    if include_cuerpo:
        select_cols += ", cuerpo"
    query = f"SELECT {select_cols} FROM requisiciones.email_log"
    filtros = []
    params = {}
    if destinatario:
        filtros.append("destinatario = :destinatario")
        params["destinatario"] = destinatario
    if idrequisicion:
        filtros.append("idrequisicion = :idrequisicion")
        params["idrequisicion"] = idrequisicion
    if estado:
        filtros.append("estado = :estado")
        params["estado"] = estado
    if from_:
        filtros.append("fecha_envio::date >= :from")
        params["from"] = from_
    if to:
        filtros.append("fecha_envio::date <= :to")
        params["to"] = to
    if q:
        filtros.append("(asunto ILIKE :q OR cuerpo ILIKE :q)")
        params["q"] = f"%{q}%"
    if filtros:
        query += " WHERE " + " AND ".join(filtros)
    query += " ORDER BY fecha_envio DESC"

    rows = db.execute(text(query), params).fetchall()

    # Construir CSV en memoria
    buffer = StringIO()
    writer = csv.writer(buffer)
    headers = ["idlog", "fecha_envio", "destinatario", "asunto", "estado", "error", "idrequisicion"]
    if include_cuerpo:
        headers.append("cuerpo")
    writer.writerow(headers)
    for r in rows:
        d = dict(r._mapping)
        row_out = [
            d.get("idlog"),
            d.get("fecha_envio"),
            d.get("destinatario"),
            d.get("asunto"),
            d.get("estado"),
            d.get("error"),
            d.get("idrequisicion"),
        ]
        if include_cuerpo:
            row_out.append(d.get("cuerpo"))
        writer.writerow(row_out)

    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=email_log.csv"
        },
    )

@router.post("/email-log/{idlog}/reenviar", summary="Reenviar correo con error")
async def api_reenviar_email(
    idlog: int,
    db: Session = Depends(get_db),
):
    """
    Reenv??a un correo que tuvo error. Busca los datos originales en email_log
    y vuelve a intentar el env??o.
    """
    try:
        # Obtener datos del log original
        query = text("""
            SELECT el.destinatario, el.asunto, el.cuerpo, el.idrequisicion,
                   r.codrequisicion
            FROM requisiciones.email_log el
            LEFT JOIN requisiciones.requisiciones r ON el.idrequisicion = r.idrequisicion
            WHERE el.idlog = :idlog AND el.estado = 'error'
            LIMIT 1
        """)
        row = db.execute(query, {"idlog": idlog}).fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Log no encontrado o no tiene error")
        
        from app.core.mail import send_email
        import os
        
        destinatario = row.destinatario
        asunto = row.asunto
        cuerpo_text = row.cuerpo or ""
        idrequisicion = row.idrequisicion
        codrequisicion = row.codrequisicion
        prointermedio = None
        profinal = None
        
        # Reconstruir HTML y attachments si es necesario
        inline_images = {}
        try:
            logo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "Imagen", "LogoSedhEscudo.png"))
            with open(logo_path, "rb") as f:
                inline_images["logo_sedh"] = f.read()
        except Exception:
            pass
        
        # Determinar tipo de correo por el asunto
        cuerpo_html = None
        attachments = []
        
        if "Confirmaci??n de creaci??n" in asunto:
            link_hist = f"http://192.168.180.164:8081/historial?cod={codrequisicion or ''}&tab=aprobaciones"
            cuerpo_html = f"""
            <div style='font-family:Segoe UI, Tahoma, sans-serif; color:#103b37;'>
              <div style='display:flex;align-items:center;gap:12px;margin-bottom:16px;'>
                <img src="cid:logo_sedh" alt="SEDH" style="height:60px;">
                <div>
                  <div style='font-weight:600;font-size:18px;'>Secretar??a de Derechos Humanos - Sistema de Almac??n</div>
                  <div style='font-size:12px;opacity:0.8;'>Confirmaci??n de creaci??n de requisici??n</div>
                </div>
              </div>
              <div style='background:#f8f9fa;border:1px solid #e0e0e0;border-radius:8px;padding:16px;'>
                <div style='margin-bottom:12px;'>Tu requisici??n {codrequisicion or ''} fue creada correctamente y enviada para aprobaci??n.</div>
                                <div style='margin-top:8px;'>
                                    <div><strong>Programa Intermedio:</strong> {str(prointermedio) if prointermedio is not None else 'N/A'}</div>
                                    <div><strong>Programa Final:</strong> {str(profinal) if profinal is not None else 'N/A'}</div>
                                </div>
                <a href='{link_hist}' style='display:inline-block;background:#0f766e;color:white;text-decoration:none;padding:10px 16px;border-radius:6px;'>Ver historial y aprobaciones</a>
              </div>
              <div style='font-size:12px;color:#6c757d;margin-top:12px;'>Este correo se genera autom??ticamente. No responder.</div>
            </div>
            """
        elif "pendiente de aprobaci??n" in asunto:
            link_aprobacion = f"http://192.168.180.164:8081/requisiciones/aprobar/{codrequisicion or ''}"
            cuerpo_html = f"""
            <div style='font-family:Segoe UI, Tahoma, sans-serif; color:#103b37;'>
              <div style='display:flex;align-items:center;gap:12px;margin-bottom:16px;'>
                <img src="cid:logo_sedh" alt="SEDH" style="height:60px;">
                <div>
                  <div style='font-weight:600;font-size:18px;'>Secretar??a de Derechos Humanos - Sistema de Almac??n</div>
                  <div style='font-size:12px;opacity:0.8;'>Notificaci??n autom??tica del sistema</div>
                </div>
              </div>
              <div style='background:#f8f9fa;border:1px solid #e0e0e0;border-radius:8px;padding:16px;'>
                <div style='margin-bottom:12px;'>Tiene una nueva requisici??n pendiente de aprobaci??n.</div>
                <div><strong>C??digo:</strong> {codrequisicion or 'N/A'}</div>
                                <div style='margin-top:8px;'>
                                    <div><strong>Programa Intermedio:</strong> {str(prointermedio) if prointermedio is not None else 'N/A'}</div>
                                    <div><strong>Programa Final:</strong> {str(profinal) if profinal is not None else 'N/A'}</div>
                                </div>
                <a href='{link_aprobacion}' style='display:inline-block;background:#0f766e;color:white;text-decoration:none;padding:10px 16px;border-radius:6px;margin-top:10px;'>Revisar y aprobar</a>
              </div>
              <div style='font-size:12px;color:#6c757d;margin-top:12px;'>Este correo se genera autom??ticamente. No responder.</div>
            </div>
            """
        
        # Reenviar
        estado, error = send_email(
            destinatario,
            asunto,
            cuerpo_text,
            body_html=cuerpo_html,
            attachments=attachments,
            inline_images=inline_images,
        )
        
        # Registrar nuevo intento
        registrar_email_log(destinatario, asunto, cuerpo_text, estado, error, idrequisicion, db)
        
        return {"estado": estado, "error": error, "idlog": idlog}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error al reenviar correo: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/programas-cascading", summary="Obtener relaci??n entre programas intermedios y finales")
async def api_programas_cascading(db: Session = Depends(get_db)):
    """
    Devuelve la relaci??n entre programas intermedios y programas finales
    para implementar cascada en los dropdowns del formulario de requisiciones.
    """
    try:
        query = text("""
            SELECT 
                pi.idprointermedio,
                pi.codigo AS codigo_pi,
                pi.descripcion AS programa_intermedio,
                pg.idprograma,
                pg.codigo AS codigo_pf,
                pg.descripcion AS programa_final
            FROM requisiciones.prointermedios pi
            LEFT JOIN requisiciones.programas pg
                   ON pi.idprograma = pg.idprograma
            ORDER BY pg.idprograma, pi.idprointermedio
        """)
        rows = db.execute(query).fetchall()
        
        # Agrupar por programa final para facilitar la b??squeda
        programas_finales = {}
        programas_intermedios = []
        
        for row in rows:
            row_dict = dict(row._mapping)
            
            # Agregar programa intermedio
            programas_intermedios.append({
                "idprointermedio": row_dict["idprointermedio"],
                "codigo_pi": row_dict["codigo_pi"],
                "programa_intermedio": row_dict["programa_intermedio"],
                "idprograma": row_dict["idprograma"],
                "codigo_pf": row_dict["codigo_pf"],
                "programa_final": row_dict["programa_final"]
            })
            
            # Crear ??ndice de programas finales ??nicos
            if row_dict["idprograma"] and row_dict["idprograma"] not in programas_finales:
                programas_finales[row_dict["idprograma"]] = {
                    "idprograma": row_dict["idprograma"],
                    "codigo": row_dict["codigo_pf"],
                    "descripcion": row_dict["programa_final"]
                }
        
        return {
            "programas_intermedios": programas_intermedios,
            "programas_finales": list(programas_finales.values())
        }
        
    except Exception as e:
        print(f"Error al obtener programas cascading: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/buscar-por-codigo", summary="Buscar requisici??n por c??digo")
async def api_buscar_por_codigo(
    codigo: str,
    db: Session = Depends(get_db),
):
    """
    Busca una requisici??n por su c??digo (ej: UIT-050-2025) y retorna su ID.
    """
    query = text("""
        SELECT idrequisicion, codrequisicion, nomempleado, fechacreacion
        FROM requisiciones.requisiciones
        WHERE codrequisicion = :codigo
        LIMIT 1
    """)
    row = db.execute(query, {"codigo": codigo}).fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail=f"No se encontr?? requisici??n con c??digo {codigo}")
    
    return {
        "idrequisicion": str(row.idrequisicion),
        "codrequisicion": row.codrequisicion,
        "nomempleado": row.nomempleado,
        "fechacreacion": str(row.fechacreacion),
    }

from app.repositories.requisiciones import crear_requisicion, requisiciones_pendientes_jefe, responder_requisicion_jefe
from app.repositories.requisiciones import requisiciones_pendientes_gerente
from app.repositories.requisiciones import responder_requisicion_gerente
from app.repositories.requisiciones import requisiciones_pendientes_jefe_materiales
from app.repositories.requisiciones import responder_requisicion_jefe_materiales
from app.repositories.requisiciones import requisiciones_pendientes_almacen
from app.repositories.requisiciones import responder_requisicion_almacen
from app.repositories.requisiciones import registrar_auditoria_requisicion, actualizar_timestamp_aprobacion_jefe, actualizar_timestamp_aprobacion_almacen, actualizar_timestamp_rechazo, actualizar_timestamp_envio
from app.schemas.requisiciones.schemas import CrearRequisicionIn, CrearRequisicionOut, ResponderRequisicionIn, ResponderRequisicionOut
from app.schemas.requisiciones.schemas import RequisicionPendienteOut
from app.schemas.requisiciones.schemas import RequisicionPendienteGerenteOut
from app.schemas.requisiciones.schemas import ResponderRequisicionGerenteIn

#EMPLEADOS 

@router.get("/carrito-info", summary="Informaci??n del carrito del usuario autenticado")
async def api_carrito_info(
    current_user: dict = Depends(get_current_user),
):
    """
    Endpoint para verificar la identidad del usuario y su carrito.
    ??til para el sistema de carrito individual.
    """
    email = (str(current_user.get("email") or current_user.get("sub") or "")).strip()
    if not email:
        raise HTTPException(status_code=401, detail="No se encontr?? email del usuario autenticado")
    
    return {
        "email": email,
        "usuario": current_user.get("nombre", email),
        "rol": current_user.get("role", "Empleado"),
        "carrito_clave_productos": f"cart_productos_{email}",
        "carrito_clave_categorias": f"cart_categorias_{email}",
        "mensaje": f"Carrito individual habilitado para {email}"
    }

@router.get("/mis-requisiciones", summary="Ver mis propias requisiciones", response_model=list[dict])
async def api_mis_requisiciones(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Endpoint para que cada usuario vea sus propias requisiciones con el estado de aprobaci??n"""
    email = (str(current_user.get("email") or current_user.get("sub") or "")).strip()
    if not email:
        raise HTTPException(status_code=401, detail="No se encontr?? email del usuario autenticado")
    
    try:
        # Consulta SQL para obtener las requisiciones del usuario con TODOS los detalles
        query = text("""
        SELECT 
            r.idrequisicion,
            r.codrequisicion,
            r.nomempleado,
            r.iddependencia,
            r.fecsolicitud,
            r.codprograma,
            r.prointermedio,
            r.profinal,
            r.estgeneral,
            r.obsempleado,
            r.obsalmacen,
            r.motrechazo,
            r.gastotaldelpedido,
            r.reqentregadopor,
            r.reqrecibidopor,
            r.creadoen,
            r.creadopor,
            r.actualizadoen,
            r.actualizadopor,
            r.fecha_hora_creacion AT TIME ZONE 'America/Tegucigalpa' AS fecha_hora_creacion,
            r.fecha_hora_envio AT TIME ZONE 'America/Tegucigalpa' AS fecha_hora_envio,
            r.fecha_hora_aprobacion_jefe AT TIME ZONE 'America/Tegucigalpa' AS fecha_hora_aprobacion_jefe,
            r.fecha_hora_aprobacion_almacen AT TIME ZONE 'America/Tegucigalpa' AS fecha_hora_aprobacion_almacen,
            r.fecha_hora_entrega AT TIME ZONE 'America/Tegucigalpa' AS fecha_hora_entrega,
            r.fecha_hora_rechazo AT TIME ZONE 'America/Tegucigalpa' AS fecha_hora_rechazo,
                        -- Nombres de posibles aprobadores por rol
                        (
                                SELECT jefe.nombre
                                FROM usuarios.empleados e
                                LEFT JOIN usuarios.empleados jefe ON jefe.dni = e.dnijefeinmediato
                                WHERE e.emailinstitucional = r.CreadoPor
                                LIMIT 1
                        ) AS NombreJefeInmediato,
                        (
                            SELECT string_agg(ea.nombre, ', ' ORDER BY ea.nombre)
                            FROM usuarios.empleados ea
                            JOIN acceso.empleados_roles era ON era.emailinstitucional = ea.emailinstitucional AND COALESCE(era.actlaboralmente, TRUE) = TRUE
                            JOIN acceso.roles ra ON ra.idrol = era.idrol AND ra.nomrol = 'GerAdmon'
                        ) AS ListaGerentesAdmin,
                        (
                            SELECT string_agg(em.nombre, ', ' ORDER BY em.nombre)
                            FROM usuarios.empleados em
                            JOIN acceso.empleados_roles erm ON erm.emailinstitucional = em.emailinstitucional AND COALESCE(erm.actlaboralmente, TRUE) = TRUE
                            JOIN acceso.roles rm ON rm.idrol = erm.idrol AND rm.nomrol = 'JefSerMat'
                        ) AS ListaJefeMateriales,
                        (
                            SELECT string_agg(el.nombre, ', ' ORDER BY el.nombre)
                            FROM usuarios.empleados el
                            JOIN acceso.empleados_roles erl ON erl.emailinstitucional = el.emailinstitucional AND COALESCE(erl.actlaboralmente, TRUE) = TRUE
                            JOIN acceso.roles rl ON rl.idrol = erl.idrol AND rl.nomrol = 'EmpAlmacen'
                        ) AS ListaAlmacen,
            -- Estado de aprobaci??n del Jefe Inmediato
            COALESCE(
                (SELECT EstadoAprobacion 
                 FROM requisiciones.Aprobaciones a1 
                 WHERE a1.IdRequisicion = r.IdRequisicion 
                 AND a1.Rol = 'JefInmediato' 
                 ORDER BY a1.FecAprobacion DESC LIMIT 1), 
                'Pendiente'
            ) as EstadoJefeInmediato,
            -- Nombre y fecha de aprobaci??n del Jefe Inmediato
            (SELECT e.nombre FROM requisiciones.Aprobaciones a1
             JOIN usuarios.empleados e ON e.emailinstitucional = a1.EmailInstitucional
             WHERE a1.IdRequisicion = r.IdRequisicion AND a1.Rol = 'JefInmediato'
             ORDER BY a1.FecAprobacion DESC LIMIT 1) as NombreAprobadorJefe,
            (SELECT a1.FecAprobacion AT TIME ZONE 'America/Tegucigalpa' FROM requisiciones.Aprobaciones a1
             WHERE a1.IdRequisicion = r.IdRequisicion AND a1.Rol = 'JefInmediato'
             ORDER BY a1.FecAprobacion DESC LIMIT 1) as FechaAprobacionJefe,
            -- Estado de aprobaci??n del Gerente Administrativo
            COALESCE(
                (SELECT EstadoAprobacion 
                 FROM requisiciones.Aprobaciones a2 
                 WHERE a2.IdRequisicion = r.IdRequisicion 
                 AND a2.Rol = 'GerAdmon' 
                 ORDER BY a2.FecAprobacion DESC LIMIT 1), 
                'Pendiente'
            ) as EstadoGerenteAdministrativo,
            -- Nombre y fecha de aprobaci??n del Gerente
            (SELECT e.nombre FROM requisiciones.Aprobaciones a2
             JOIN usuarios.empleados e ON e.emailinstitucional = a2.EmailInstitucional
             WHERE a2.IdRequisicion = r.IdRequisicion AND a2.Rol = 'GerAdmon'
             ORDER BY a2.FecAprobacion DESC LIMIT 1) as NombreAprobadorGerente,
            (SELECT a2.FecAprobacion AT TIME ZONE 'America/Tegucigalpa' FROM requisiciones.Aprobaciones a2
             WHERE a2.IdRequisicion = r.IdRequisicion AND a2.Rol = 'GerAdmon'
             ORDER BY a2.FecAprobacion DESC LIMIT 1) as FechaAprobacionGerente,
            -- Estado de aprobaci??n del Jefe de Servicios Materiales
            COALESCE(
                (SELECT EstadoAprobacion 
                 FROM requisiciones.Aprobaciones a3 
                 WHERE a3.IdRequisicion = r.IdRequisicion 
                 AND a3.Rol = 'JefSerMat' 
                 ORDER BY a3.FecAprobacion DESC LIMIT 1), 
                'Pendiente'
            ) as EstadoJefeMateriales,
            -- Nombre y fecha de aprobaci??n del Jefe Materiales
            (SELECT e.nombre FROM requisiciones.Aprobaciones a3
             JOIN usuarios.empleados e ON e.emailinstitucional = a3.EmailInstitucional
             WHERE a3.IdRequisicion = r.IdRequisicion AND a3.Rol = 'JefSerMat'
             ORDER BY a3.FecAprobacion DESC LIMIT 1) as NombreAprobadorJefeMat,
            (SELECT a3.FecAprobacion AT TIME ZONE 'America/Tegucigalpa' FROM requisiciones.Aprobaciones a3
             WHERE a3.IdRequisicion = r.IdRequisicion AND a3.Rol = 'JefSerMat'
             ORDER BY a3.FecAprobacion DESC LIMIT 1) as FechaAprobacionJefeMat,
            -- Estado de aprobaci??n del Almac??n
            COALESCE(
                (SELECT EstadoAprobacion 
                 FROM requisiciones.Aprobaciones a4 
                 WHERE a4.IdRequisicion = r.IdRequisicion 
                 AND a4.Rol = 'EmpAlmacen' 
                 ORDER BY a4.FecAprobacion DESC LIMIT 1), 
                'Pendiente'
            ) as EstadoAlmacen,
            -- Nombre y fecha de aprobaci??n del Almac??n
            (SELECT e.nombre FROM requisiciones.Aprobaciones a4
             JOIN usuarios.empleados e ON e.emailinstitucional = a4.EmailInstitucional
             WHERE a4.IdRequisicion = r.IdRequisicion AND a4.Rol = 'EmpAlmacen'
             ORDER BY a4.FecAprobacion DESC LIMIT 1) as NombreAprobadorAlmacen,
            (SELECT a4.FecAprobacion AT TIME ZONE 'America/Tegucigalpa' FROM requisiciones.Aprobaciones a4
             WHERE a4.IdRequisicion = r.IdRequisicion AND a4.Rol = 'EmpAlmacen'
             ORDER BY a4.FecAprobacion DESC LIMIT 1) as FechaAprobacionAlmacen,
                        -- Aprobador actual (rol y nombre)
                        CASE 
                            WHEN COALESCE((SELECT EstadoAprobacion FROM requisiciones.Aprobaciones ai WHERE ai.IdRequisicion = r.IdRequisicion AND ai.Rol = 'JefInmediato' ORDER BY ai.FecAprobacion DESC LIMIT 1), 'Pendiente') = 'Pendiente'
                                THEN 'Jefe Inmediato'
                            WHEN COALESCE((SELECT EstadoAprobacion FROM requisiciones.Aprobaciones ag WHERE ag.IdRequisicion = r.IdRequisicion AND ag.Rol = 'GerAdmon' ORDER BY ag.FecAprobacion DESC LIMIT 1), 'Pendiente') = 'Pendiente'
                                THEN 'Gerente Admin.'
                            WHEN COALESCE((SELECT EstadoAprobacion FROM requisiciones.Aprobaciones aj WHERE aj.IdRequisicion = r.IdRequisicion AND aj.Rol = 'JefSerMat' ORDER BY aj.FecAprobacion DESC LIMIT 1), 'Pendiente') = 'Pendiente'
                                THEN 'Jefe Materiales'
                            WHEN COALESCE((SELECT EstadoAprobacion FROM requisiciones.Aprobaciones al WHERE al.IdRequisicion = r.IdRequisicion AND al.Rol = 'EmpAlmacen' ORDER BY al.FecAprobacion DESC LIMIT 1), 'Pendiente') = 'Pendiente'
                                THEN 'Almac??n'
                            ELSE NULL
                        END AS AprobadorActualRol,
                        CASE 
                            WHEN COALESCE((SELECT EstadoAprobacion FROM requisiciones.Aprobaciones ai2 WHERE ai2.IdRequisicion = r.IdRequisicion AND ai2.Rol = 'JefInmediato' ORDER BY ai2.FecAprobacion DESC LIMIT 1), 'Pendiente') = 'Pendiente'
                                THEN (
                                        SELECT jefe2.nombre FROM usuarios.empleados e2
                                        LEFT JOIN usuarios.empleados jefe2 ON jefe2.dni = e2.dnijefeinmediato
                                        WHERE e2.emailinstitucional = r.CreadoPor LIMIT 1
                                )
                            WHEN COALESCE((SELECT EstadoAprobacion FROM requisiciones.Aprobaciones ag2 WHERE ag2.IdRequisicion = r.IdRequisicion AND ag2.Rol = 'GerAdmon' ORDER BY ag2.FecAprobacion DESC LIMIT 1), 'Pendiente') = 'Pendiente'
                                THEN (
                                        SELECT split_part(string_agg(ea2.nombre, ', ' ORDER BY ea2.nombre), ',', 1)
                                        FROM usuarios.empleados ea2
                                        JOIN acceso.empleados_roles era2 ON era2.emailinstitucional = ea2.emailinstitucional AND COALESCE(era2.actlaboralmente, TRUE) = TRUE
                                        JOIN acceso.roles ra2 ON ra2.idrol = era2.idrol AND ra2.nomrol = 'GerAdmon'
                                )
                            WHEN COALESCE((SELECT EstadoAprobacion FROM requisiciones.Aprobaciones aj2 WHERE aj2.IdRequisicion = r.IdRequisicion AND aj2.Rol = 'JefSerMat' ORDER BY aj2.FecAprobacion DESC LIMIT 1), 'Pendiente') = 'Pendiente'
                                THEN (
                                        SELECT split_part(string_agg(em2.nombre, ', ' ORDER BY em2.nombre), ',', 1)
                                        FROM usuarios.empleados em2
                                        JOIN acceso.empleados_roles erm2 ON erm2.emailinstitucional = em2.emailinstitucional AND COALESCE(erm2.actlaboralmente, TRUE) = TRUE
                                        JOIN acceso.roles rm2 ON rm2.idrol = erm2.idrol AND rm2.nomrol = 'JefSerMat'
                                )
                            WHEN COALESCE((SELECT EstadoAprobacion FROM requisiciones.Aprobaciones al2 WHERE al2.IdRequisicion = r.IdRequisicion AND al2.Rol = 'EmpAlmacen' ORDER BY al2.FecAprobacion DESC LIMIT 1), 'Pendiente') = 'Pendiente'
                                THEN (
                                        SELECT split_part(string_agg(el2.nombre, ', ' ORDER BY el2.nombre), ',', 1)
                                        FROM usuarios.empleados el2
                                        JOIN acceso.empleados_roles erl2 ON erl2.emailinstitucional = el2.emailinstitucional AND COALESCE(erl2.actlaboralmente, TRUE) = TRUE
                                        JOIN acceso.roles rl2 ON rl2.idrol = erl2.idrol AND rl2.nomrol = 'EmpAlmacen'
                                )
                            ELSE NULL
                        END AS AprobadorActualNombre,
            -- ??ltimo comentario
            COALESCE(
                (SELECT Comentario 
                 FROM requisiciones.Aprobaciones a5 
                 WHERE a5.IdRequisicion = r.IdRequisicion 
                 ORDER BY a5.FecAprobacion DESC LIMIT 1), 
                ''
            ) as UltimoComentario
        FROM requisiciones.Requisiciones r
        WHERE r.CreadoPor = :email
        ORDER BY r.FecSolicitud DESC
        """)
        
        result = db.execute(query, {"email": email})
        requisiciones = []
        
        for row in result:
            # Usar _mapping para acceder a las columnas por nombre (min??sculas)
            row_dict = dict(row._mapping)
            id_requisicion = str(row_dict['idrequisicion'])
            
            # Obtener los productos de esta requisici??n desde Detalle_Requisicion
            query_productos = text("""
            SELECT 
                dr.IdProducto,
                dr.CantSolicitada as Cantidad,
                dr.GasUnitario as PrecioUnitario,
                dr.GasTotalProducto as Subtotal,
                p.CodObjetoUnico,
                p.NomProducto,
                p.DescProducto,
                p.Proveedor,
                p.IdUnidadMedida,
                p.GasUnitario,
                p.CanStock,
                p.FecVencimiento
            FROM requisiciones.Detalle_Requisicion dr
            INNER JOIN productos.Productos p ON dr.IdProducto = p.IdProducto
            WHERE dr.IdRequisicion = :id_requisicion
            ORDER BY p.NomProducto
            """)
            
            result_productos = db.execute(query_productos, {"id_requisicion": id_requisicion})
            productos = []
            
            for prod in result_productos:
                prod_dict = dict(prod._mapping)
                productos.append({
                    "IdProducto": str(prod_dict['idproducto']),
                    "CodObjetoUnico": prod_dict['codobjetounico'],
                    "NomProducto": prod_dict['nomproducto'],
                    "DescProducto": prod_dict['descproducto'],
                    "Proveedor": prod_dict['proveedor'],
                    "IdUnidadMedida": str(prod_dict['idunidadmedida']) if prod_dict['idunidadmedida'] else None,
                    "Cantidad": float(prod_dict['cantidad']) if prod_dict['cantidad'] else 0.0,
                    "PrecioUnitario": float(prod_dict['preciounitario']) if prod_dict['preciounitario'] else 0.0,
                    "Subtotal": float(prod_dict['subtotal']) if prod_dict['subtotal'] else 0.0,
                    "GasUnitario": float(prod_dict['gasunitario']) if prod_dict['gasunitario'] else 0.0,
                    "CanStock": float(prod_dict['canstock']) if prod_dict['canstock'] else 0.0,
                    "FecVencimiento": prod_dict['fecvencimiento'].isoformat() if prod_dict['fecvencimiento'] else None
                })
            
            # Serializar fechas con componente de hora para evitar que JS reste 6h al parsear solo la fecha
            fecha_aprob_jefe_raw = row_dict.get('fecha_hora_aprobacion_jefe') or row_dict.get('fechaaprobacionjefe')
            fecha_aprob_gerente_raw = row_dict.get('fechaaprobaciongerente')
            fecha_aprob_jefemat_raw = row_dict.get('fechaaprobacionjefemat')
            fecha_aprob_almacen_raw = row_dict.get('fecha_hora_aprobacion_almacen') or row_dict.get('fechaaprobacionalmacen')

            requisiciones.append({
                "IdRequisicion": id_requisicion,
                "CodRequisicion": row_dict['codrequisicion'],
                "NomEmpleado": row_dict['nomempleado'],
                "IdDependencia": str(row_dict['iddependencia']) if row_dict['iddependencia'] else None,
                "FecSolicitud": _iso_with_time(row_dict['fecsolicitud']) if row_dict['fecsolicitud'] else None,
                "CodPrograma": row_dict['codprograma'],
                "ProIntermedio": row_dict['prointermedio'],
                "ProFinal": row_dict['profinal'],
                "EstGeneral": row_dict['estgeneral'],
                "ObsEmpleado": row_dict['obsempleado'],
                "ObsAlmacen": row_dict['obsalmacen'],
                "MotRechazo": row_dict['motrechazo'],
                "GasTotalDelPedido": float(row_dict['gastotaldelpedido']) if row_dict['gastotaldelpedido'] else 0.0,
                "ReqEntregadoPor": row_dict['reqentregadopor'],
                "ReqRecibidoPor": row_dict['reqrecibidopor'],
                "CreadoEn": _iso_with_time(row_dict['creadoen']) if row_dict['creadoen'] else None,
                "CreadoPor": row_dict['creadopor'],
                "ActualizadoEn": _iso_with_time(row_dict['actualizadoen']) if row_dict['actualizadoen'] else None,
                "ActualizadoPor": row_dict['actualizadopor'],
                "FechaHoraCreacion": _iso_with_time(row_dict['fecha_hora_creacion']) if row_dict.get('fecha_hora_creacion') else None,
                "FechaHoraEnvio": _iso_with_time(row_dict['fecha_hora_envio']) if row_dict.get('fecha_hora_envio') else None,
                "FechaHoraAprobacionJefe": _iso_with_time(row_dict['fecha_hora_aprobacion_jefe']) if row_dict.get('fecha_hora_aprobacion_jefe') else None,
                "FechaHoraAprobacionAlmacen": _iso_with_time(row_dict['fecha_hora_aprobacion_almacen']) if row_dict.get('fecha_hora_aprobacion_almacen') else None,
                "FechaHoraEntrega": _iso_with_time(row_dict['fecha_hora_entrega']) if row_dict.get('fecha_hora_entrega') else None,
                "FechaHoraRechazo": _iso_with_time(row_dict['fecha_hora_rechazo']) if row_dict.get('fecha_hora_rechazo') else None,
                "ControlTiempos": {
                    "Creacion": _iso_with_time(row_dict['fecha_hora_creacion']) if row_dict.get('fecha_hora_creacion') else None,
                    "Envio": _iso_with_time(row_dict['fecha_hora_envio']) if row_dict.get('fecha_hora_envio') else None,
                    "AprobacionJefe": _iso_with_time(row_dict['fecha_hora_aprobacion_jefe']) if row_dict.get('fecha_hora_aprobacion_jefe') else None,
                    "AprobacionAlmacen": _iso_with_time(row_dict['fecha_hora_aprobacion_almacen']) if row_dict.get('fecha_hora_aprobacion_almacen') else None,
                    "Entrega": _iso_with_time(row_dict['fecha_hora_entrega']) if row_dict.get('fecha_hora_entrega') else None,
                    "Rechazo": _iso_with_time(row_dict['fecha_hora_rechazo']) if row_dict.get('fecha_hora_rechazo') else None
                },
                "NombreJefeInmediato": row_dict.get('nombrejefeinmediato'),
                "ListaGerentesAdmin": row_dict.get('listagerentesadmin'),
                "ListaJefeMateriales": row_dict.get('listajefemateriales'),
                "ListaAlmacen": row_dict.get('listaalmacen'),
                "EstadoJefeInmediato": row_dict['estadojefeinmediato'],
                "EstadoGerenteAdministrativo": row_dict['estadogerenteadministrativo'],
                "EstadoJefeMateriales": row_dict['estadojefemateriales'],
                "EstadoAlmacen": row_dict['estadoalmacen'],
                "AprobadorActualRol": row_dict.get('aprobadoractualrol'),
                "AprobadorActualNombre": row_dict.get('aprobadoractualnombre'),
                "UltimoComentario": row_dict['ultimocomentario'],
                "Productos": productos,
                "TotalProductos": len(productos),
                "FlujoAprobacion": {
                    "JefeInmediato": row_dict['estadojefeinmediato'],
                    "GerenteAdministrativo": row_dict['estadogerenteadministrativo'],
                    "JefeServiciosMateriales": row_dict['estadojefemateriales'],
                    "Almacen": row_dict['estadoalmacen']
                },
                "DetalleAprobaciones": {
                    "JefeInmediato": {
                        "Estado": row_dict['estadojefeinmediato'],
                        "NombreAprobador": row_dict.get('nombreaprobadorjefe'),
                        "FechaAprobacion": _iso_with_time(fecha_aprob_jefe_raw)
                    },
                    "GerenteAdministrativo": {
                        "Estado": row_dict['estadogerenteadministrativo'],
                        "NombreAprobador": row_dict.get('nombreaprobadorgerente'),
                        "FechaAprobacion": _iso_with_time(fecha_aprob_gerente_raw)
                    },
                    "JefeServiciosMateriales": {
                        "Estado": row_dict['estadojefemateriales'],
                        "NombreAprobador": row_dict.get('nombreaprobadorjefemat'),
                        "FechaAprobacion": _iso_with_time(fecha_aprob_jefemat_raw)
                    },
                    "Almacen": {
                        "Estado": row_dict['estadoalmacen'],
                        "NombreAprobador": row_dict.get('nombreaprobadoralmacen'),
                        "FechaAprobacion": _iso_with_time(fecha_aprob_almacen_raw)
                    }
                }
            })
        
        return requisiciones
        
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")

@router.get("/jerarquia", summary="Ver jerarqu??a de aprobaci??n del usuario")
async def api_jerarquia_usuario(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Endpoint para mostrar la jerarqu??a de aprobaci??n seg??n el usuario"""
    email = (str(current_user.get("email") or current_user.get("sub") or "")).strip()
    if not email:
        raise HTTPException(status_code=401, detail="No se encontr?? email del usuario autenticado")
    
    try:
        # Consulta para obtener la informaci??n del empleado y su jerarqu??a
        query = text("""
        SELECT 
            e.EmailInstitucional,
            e.Nombre as NombreEmpleado,
            e.DNI,
            e.DNIJefeInmediato,
            d.NomDependencia,
            d.Siglas as SiglasDependencia,
            -- Informaci??n del Jefe Inmediato
            jefe.EmailInstitucional as EmailJefeInmediato,
            jefe.Nombre as NombreJefeInmediato,
            -- Roles del usuario actual
            ARRAY_AGG(DISTINCT r.NomRol) as Roles
        FROM usuarios.Empleados e
        LEFT JOIN usuarios.Dependencias d ON e.IdDependencia = d.IdDependencia
        LEFT JOIN usuarios.Empleados jefe ON jefe.DNI = e.DNIJefeInmediato
        LEFT JOIN acceso.EmpleadoRoles er ON er.EmailInstitucional = e.EmailInstitucional
        LEFT JOIN acceso.Roles r ON r.IdRol = er.IdRol
        WHERE e.EmailInstitucional = :email
        GROUP BY e.EmailInstitucional, e.Nombre, e.DNI, e.DNIJefeInmediato, 
                 d.NomDependencia, d.Siglas, jefe.EmailInstitucional, jefe.Nombre
        """)
        
        result = db.execute(query, {"email": email}).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # Definir el flujo de aprobaci??n est??ndar
        flujo_aprobacion = [
            {
                "paso": 1,
                "rol": "Empleado",
                "descripcion": "Crear requisici??n",
                "nombre": result.NombreEmpleado,
                "email": result.EmailInstitucional,
                "estado": "Completado"
            },
            {
                "paso": 2,
                "rol": "Jefe Inmediato",
                "descripcion": "Primera aprobaci??n",
                "nombre": result.NombreJefeInmediato or "Sin asignar",
                "email": result.EmailJefeInmediato or "Sin asignar",
                "estado": "Pendiente"
            },
            {
                "paso": 3,
                "rol": "Gerente Administrativo",
                "descripcion": "Segunda aprobaci??n",
                "nombre": "Por determinar",
                "email": "Por determinar",
                "estado": "Pendiente"
            },
            {
                "paso": 4,
                "rol": "Jefe de Servicios Materiales",
                "descripcion": "Aprobaci??n final",
                "nombre": "Por determinar",
                "email": "Por determinar",
                "estado": "Pendiente"
            }
        ]
        
        return {
            "usuario": {
                "email": result.EmailInstitucional,
                "nombre": result.NombreEmpleado,
                "dni": result.DNI,
                "dependencia": result.NomDependencia,
                "siglas": result.SiglasDependencia,
                "roles": result.Roles or []
            },
            "jerarquia": {
                "jefe_inmediato": {
                    "email": result.EmailJefeInmediato,
                    "nombre": result.NombreJefeInmediato,
                    "dni": result.DNIJefeInmediato
                }
            },
            "flujo_aprobacion": flujo_aprobacion,
            "descripcion": "Las requisiciones siguen este flujo: Empleado ??? Jefe Inmediato ??? Gerente Administrativo ??? Jefe de Servicios Materiales"
        }
        
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")

def registrar_email_log(destinatario, asunto, cuerpo, estado, error, idrequisicion, db):
    try:
        db.execute(text("""
            INSERT INTO requisiciones.email_log (idrequisicion, destinatario, asunto, cuerpo, estado, error)
            VALUES (:idrequisicion, :destinatario, :asunto, :cuerpo, :estado, :error)
        """), {
            "idrequisicion": str(idrequisicion),
            "destinatario": destinatario,
            "asunto": asunto,
            "cuerpo": cuerpo,
            "estado": estado,
            "error": error or None
        })
        db.commit()
    except Exception as logerr:
        print(f"ERROR al registrar email_log: {logerr}")

@router.post("/", summary="Crear requisici??n", response_model=CrearRequisicionOut)
@router.post("", include_in_schema=False)
async def api_crear_requisicion(
    body: CrearRequisicionIn,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    email = (str(current_user.get("email") or current_user.get("sub") or "")).strip()
    if not email:
        raise HTTPException(status_code=401, detail="No se encontr?? email del usuario autenticado")
    
    try:
        body = body.model_copy(update={"email": email})
        
        # DEBUG: Imprimir productos recibidos
        print(f"\n???? DEBUG - Productos recibidos en API:")
        for idx, prod in enumerate(body.productos):
            print(f"  Producto {idx}: idProducto={prod.idProducto}, nombre={prod.nombre}")
        
        result = crear_requisicion(db, body)

        # Registrar timestamps y auditor??a de creaci??n/env??o
        try:
            actualizar_timestamp_envio(db, str(result.idrequisicion), str(current_user.get("id") or ""))

            registrar_auditoria_requisicion(
                db=db,
                id_requisicion=str(result.idrequisicion),
                tipo_accion="CREADA",
                id_usuario_accion=str(current_user.get("id") or ""),
                nombre_usuario_accion=current_user.get("nombre", email),
                descripcion_accion="Requisici??n creada por solicitante",
                observaciones=None
            )

            registrar_auditoria_requisicion(
                db=db,
                id_requisicion=str(result.idrequisicion),
                tipo_accion="ENVIADA",
                id_usuario_accion=str(current_user.get("id") or ""),
                nombre_usuario_accion=current_user.get("nombre", email),
                descripcion_accion="Requisici??n enviada para aprobaci??n",
                observaciones=None
            )
        except Exception as audit_err:
            print(f"Advertencia: Error al registrar auditor??a/env??o: {audit_err}")

        # Crear notificaciones persistentes para el solicitante y su Jefe Inmediato
        try:
            # Obtener c??digo de requisici??n y nombre del solicitante (por si el resultado no lo trae)
            cod_req = getattr(result, "codrequisicion", None)
            nom_empleado = None
            if not cod_req or not getattr(result, "idrequisicion", None):
                # Fallback: consultar DB
                q_req = text("""
                    SELECT codrequisicion, nomempleado
                    FROM requisiciones.requisiciones
                    WHERE idrequisicion = :id
                """)
                row_req = db.execute(q_req, {"id": str(result.idrequisicion)}).fetchone()
                if row_req:
                    cod_req = row_req.codrequisicion
                    nom_empleado = row_req.nomempleado
            # Si no se obtuvo nombre, usar el del usuario autenticado
            nom_empleado = nom_empleado or (str(current_user.get("nombre") or "").strip() or email)

            # Buscar email del Jefe Inmediato del solicitante
            q_jefe = text("""
                SELECT jefe.emailinstitucional AS email_jefe, jefe.nombre AS nombre_jefe
                FROM usuarios.empleados e
                LEFT JOIN usuarios.empleados jefe ON jefe.dni = e.dnijefeinmediato
                WHERE e.emailinstitucional = :email
                LIMIT 1
            """)
            row_jefe = db.execute(q_jefe, {"email": email}).fetchone()
            email_jefe = row_jefe.email_jefe if row_jefe else None
            nombre_jefe = row_jefe.nombre_jefe if row_jefe else None
            
            print(f"DEBUG: Solicitante email: {email}")
            print(f"DEBUG: Jefe encontrado - email: {email_jefe}, nombre: {nombre_jefe}")

            # Notificaci??n para el Jefe Inmediato (si existe)
            if email_jefe:
                msg_jefe = f"???? Nueva requisici??n {cod_req or ''} de {nom_empleado} pendiente de aprobaci??n"
                db.execute(
                    text("""
                        INSERT INTO requisiciones.notificaciones (emailusuario, tipo, mensaje, idrequisicion, leida, fechacreacion)
                        VALUES (:email, :tipo, :mensaje, :idrequisicion, FALSE, CURRENT_TIMESTAMP)
                    """),
                    {
                        "email": email_jefe,
                        "tipo": "requisicion_nueva",
                        "mensaje": msg_jefe,
                        "idrequisicion": str(result.idrequisicion),
                    }
                )

                # Enviar correo al jefe con link de aprobaci??n
                try:
                    from app.core.mail import send_email
                    import os
                    link_aprobacion = f"http://192.168.180.164:8081/requisiciones/aprobar/{cod_req}"
                    asunto = "Requisici??n pendiente de aprobaci??n"

                    # Texto plano
                    cuerpo_text = (
                        f"SEDH Almac??n\n\n"
                        f"Nueva requisici??n pendiente de aprobaci??n.\n"
                        f"Solicitante: {nom_empleado}\n"
                        f"C??digo: {cod_req}\n\n"
                        f"Aprobar en: {link_aprobacion}\n"
                    )

                    # Cargar logo inline
                    inline_images = {}
                    try:
                        logo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "Imagen", "LogoSedhEscudo.png"))
                        with open(logo_path, "rb") as f:
                            inline_images["logo_sedh"] = f.read()
                    except Exception:
                        inline_images = {}

                    # HTML
                    cuerpo_html = f"""
                    <div style='font-family:Segoe UI, Tahoma, sans-serif; color:#103b37;'>
                      <div style='display:flex;align-items:center;gap:12px;margin-bottom:16px;'>
                        <img src="cid:logo_sedh" alt="SEDH" style="height:60px;">
                        <div>
                          <div style='font-weight:600;font-size:18px;'>Secretar??a de Derechos Humanos - Sistema de Almac??n</div>
                          <div style='font-size:12px;opacity:0.8;'>Notificaci??n autom??tica del sistema</div>
                        </div>
                      </div>
                      <div style='background:#f8f9fa;border:1px solid #e0e0e0;border-radius:8px;padding:16px;'>
                        <div style='font-size:16px;margin-bottom:8px;'>Estimado/a {nombre_jefe or ''},</div>
                        <div style='margin-bottom:12px;'>Tiene una nueva requisici??n pendiente de aprobaci??n.</div>
                        <div><strong>Solicitante:</strong> {nom_empleado}</div>
                        <div><strong>C??digo:</strong> {cod_req}</div>
                        
                        <a href='{link_aprobacion}' style='display:inline-block;background:#0f766e;color:white;text-decoration:none;padding:10px 16px;border-radius:6px;margin-top:10px;'>Revisar y aprobar</a>
                      </div>
                      <div style='font-size:12px;color:#6c757d;margin-top:12px;'>Este correo se genera autom??ticamente. No responder.</div>
                    </div>
                    """

                    # Adjuntar PDF de requisici??n - generar directamente con detalles completos
                    attachments = []
                    try:
                        if result.idrequisicion:
                            from io import BytesIO
                            from reportlab.lib.pagesizes import letter
                            from reportlab.lib import colors
                            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
                            from reportlab.lib.units import inch
                            from reportlab.lib.enums import TA_CENTER, TA_LEFT
                            from datetime import datetime
                            
                            # Consultar productos de la requisici??n
                            q_prods = text("""
                                SELECT p.nomproducto, dr.cantsolicitada, dr.gasunitario, dr.gastotalproducto
                                FROM requisiciones.detalle_requisicion dr
                                JOIN productos.productos p ON dr.idproducto = p.idproducto
                                WHERE dr.idrequisicion = :id
                                ORDER BY p.nomproducto
                            """)
                            prods_result = db.execute(q_prods, {"id": str(result.idrequisicion)}).fetchall()
                            
                            buffer = BytesIO()
                            doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=0.75*inch, leftMargin=0.75*inch, topMargin=1*inch, bottomMargin=0.75*inch)
                            elements = []
                            styles = getSampleStyleSheet()
                            
                            title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor('#1a365d'), spaceAfter=12, alignment=TA_CENTER, fontName='Helvetica-Bold')
                            subtitle_style = ParagraphStyle('CustomSubtitle', parent=styles['Heading2'], fontSize=12, textColor=colors.HexColor('#2d3748'), spaceAfter=10, fontName='Helvetica-Bold')
                            
                            # Encabezado
                            elements.append(Paragraph("SISTEMA DE ALMAC??N - SEDH", title_style))
                            elements.append(Paragraph(f"REQUISICI??N DE MATERIALES", subtitle_style))
                            elements.append(Spacer(1, 0.3*inch))
                            
                            # Informaci??n general
                            info_data = [
                                ['C??digo:', cod_req or 'N/A', 'Fecha:', datetime.now().strftime('%d/%m/%Y')],
                                ['Solicitante:', nom_empleado or 'N/A', 'Total:', f"Bs. {float(body.gasTotalPedido or 0):.2f}"]
                            ]
                            info_table = Table(info_data, colWidths=[1.2*inch, 2.8*inch, 1.0*inch, 1.5*inch])
                            info_table.setStyle(TableStyle([
                                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e2e8f0')),
                                ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#e2e8f0')),
                                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                                ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
                                ('FONTSIZE', (0, 0), (-1, -1), 9),
                                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                            ]))
                            elements.append(info_table)
                            elements.append(Spacer(1, 0.3*inch))
                            
                            # Tabla de productos
                            elements.append(Paragraph("PRODUCTOS SOLICITADOS", subtitle_style))
                            products_data = [['#', 'Producto', 'Cantidad', 'Precio Unit.', 'Total']]
                            for idx, prod in enumerate(prods_result, 1):
                                products_data.append([
                                    str(idx),
                                    prod[0] or 'N/A',
                                    str(float(prod[1] or 0)),
                                    f"Bs. {float(prod[2] or 0):.2f}",
                                    f"Bs. {float(prod[3] or 0):.2f}"
                                ])
                            
                            products_table = Table(products_data, colWidths=[0.4*inch, 3.5*inch, 0.8*inch, 1.0*inch, 1.0*inch])
                            products_table.setStyle(TableStyle([
                                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
                                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                ('ALIGN', (1, 1), (1, -1), 'LEFT'),
                                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                ('FONTSIZE', (0, 0), (-1, 0), 10),
                                ('FONTSIZE', (0, 1), (-1, -1), 9),
                                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')]),
                            ]))
                            elements.append(products_table)
                            elements.append(Spacer(1, 0.2*inch))
                            
                            # Pie de p??gina
                            footer = Paragraph(
                                f"Documento generado el {datetime.now().strftime('%d/%m/%Y a las %H:%M')} - Sistema de Almac??n SEDH",
                                ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey, alignment=TA_CENTER)
                            )
                            elements.append(footer)
                            
                            doc.build(elements)
                            buffer.seek(0)
                            attachments.append((f"Requisicion_{cod_req}.pdf", buffer.read(), "application/pdf"))
                    except Exception as pdf_err:
                        print(f"WARN: No se pudo generar PDF para adjuntar: {pdf_err}")
                        import traceback
                        traceback.print_exc()
                        pass

                    estado, error = send_email(
                        email_jefe,
                        asunto,
                        cuerpo_text,
                        body_html=cuerpo_html,
                        attachments=attachments,
                        inline_images=inline_images,
                    )
                    registrar_email_log(email_jefe, asunto, cuerpo_text, estado, error, result.idrequisicion, db)
                    if estado == "enviado":
                        print(f"Correo enviado correctamente al jefe ({email_jefe}) para requisici??n {cod_req}")
                    else:
                        print(f"ERROR al enviar correo al jefe ({email_jefe}): {error}")
                except Exception as correo_err:
                    print(f"EXCEPCI??N al enviar correo al jefe: {correo_err}")

            # Notificaci??n de confirmaci??n para el solicitante
            msg_solicitante = f"??? Tu requisici??n {cod_req or ''} fue creada y enviada para aprobaci??n"
            db.execute(
                text("""
                    INSERT INTO requisiciones.notificaciones (emailusuario, tipo, mensaje, idrequisicion, leida, fechacreacion)
                    VALUES (:email, :tipo, :mensaje, :idrequisicion, FALSE, CURRENT_TIMESTAMP)
                """),
                {
                    "email": email,
                    "tipo": "requisicion_creada",
                    "mensaje": msg_solicitante,
                    "idrequisicion": str(result.idrequisicion),
                }
            )

            # Enviar correo al solicitante a su emailinstitucional (si existe)
            try:
                from app.core.mail import send_email
                import os
                # Obtener emailinstitucional confiable desde tabla empleados
                q_emp = text("""
                    SELECT emailinstitucional, nombre
                    FROM usuarios.empleados
                    WHERE emailinstitucional = :email
                    LIMIT 1
                """)
                row_emp = db.execute(q_emp, {"email": email}).fetchone()
                correo_dest = (row_emp.emailinstitucional if row_emp else email) or email
                nombre_dest = (row_emp.nombre if row_emp else nom_empleado) or email

                asunto_solic = "Confirmaci??n de creaci??n de requisici??n"
                link_hist = f"http://localhost:8081/historial?cod={cod_req or ''}&tab=aprobaciones"
                cuerpo_text_solic = (
                    f"SEDH Almac??n\n\n"
                    f"Tu requisici??n {cod_req or ''} fue creada correctamente y enviada para aprobaci??n.\n"
                    f"Historial y aprobaciones: {link_hist}\n"
                )

                inline_images = {}
                try:
                    logo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "Imagen", "LogoSedhEscudo.png"))
                    with open(logo_path, "rb") as f:
                        inline_images["logo_sedh"] = f.read()
                except Exception:
                    inline_images = {}

                cuerpo_html_solic = f"""
                <div style='font-family:Segoe UI, Tahoma, sans-serif; color:#103b37;'>
                  <div style='display:flex;align-items:center;gap:12px;margin-bottom:16px;'>
                    <img src="cid:logo_sedh" alt="SEDH" style="height:60px;">
                    <div>
                      <div style='font-weight:600;font-size:18px;'>Secretar??a de Derechos Humanos - Sistema de Almac??n</div>
                      <div style='font-size:12px;opacity:0.8;'>Confirmaci??n de creaci??n de requisici??n</div>
                    </div>
                  </div>
                  <div style='background:#f8f9fa;border:1px solid #e0e0e0;border-radius:8px;padding:16px;'>
                    <div style='font-size:16px;margin-bottom:8px;'>Estimado/a {nombre_dest},</div>
                    <div style='margin-bottom:12px;'>Tu requisici??n {cod_req or ''} fue creada correctamente y enviada para aprobaci??n.</div>
                    <a href='{link_hist}' style='display:inline-block;background:#0f766e;color:white;text-decoration:none;padding:10px 16px;border-radius:6px;'>Ver historial y aprobaciones</a>
                  </div>
                  <div style='font-size:12px;color:#6c757d;margin-top:12px;'>Este correo se genera autom??ticamente. No responder.</div>
                </div>
                """

                attachments = []
                try:
                    if result.idrequisicion:
                        from io import BytesIO
                        from reportlab.lib.pagesizes import letter
                        from reportlab.lib import colors
                        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
                        from reportlab.lib.units import inch
                        from reportlab.lib.enums import TA_CENTER, TA_LEFT
                        from datetime import datetime
                        
                        # Consultar productos de la requisici??n
                        q_prods = text("""
                            SELECT p.nomproducto, dr.cantsolicitada, dr.gasunitario, dr.gastotalproducto
                            FROM requisiciones.detalle_requisicion dr
                            JOIN productos.productos p ON dr.idproducto = p.idproducto
                            WHERE dr.idrequisicion = :id
                            ORDER BY p.nomproducto
                        """)
                        prods_result = db.execute(q_prods, {"id": str(result.idrequisicion)}).fetchall()
                        
                        buffer = BytesIO()
                        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=0.75*inch, leftMargin=0.75*inch, topMargin=1*inch, bottomMargin=0.75*inch)
                        elements = []
                        styles = getSampleStyleSheet()
                        
                        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor('#1a365d'), spaceAfter=12, alignment=TA_CENTER, fontName='Helvetica-Bold')
                        subtitle_style = ParagraphStyle('CustomSubtitle', parent=styles['Heading2'], fontSize=12, textColor=colors.HexColor('#2d3748'), spaceAfter=10, fontName='Helvetica-Bold')
                        
                        # Encabezado
                        elements.append(Paragraph("SISTEMA DE ALMAC??N - SEDH", title_style))
                        elements.append(Paragraph(f"REQUISICI??N DE MATERIALES", subtitle_style))
                        elements.append(Spacer(1, 0.3*inch))
                        
                        # Informaci??n general
                        info_data = [
                            ['C??digo:', cod_req or 'N/A', 'Fecha:', datetime.now().strftime('%d/%m/%Y')],
                            ['Solicitante:', nombre_dest or 'N/A', 'Total:', f"Bs. {float(body.gasTotalPedido or 0):.2f}"]
                        ]
                        info_table = Table(info_data, colWidths=[1.2*inch, 2.8*inch, 1.0*inch, 1.5*inch])
                        info_table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e2e8f0')),
                            ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#e2e8f0')),
                            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, -1), 9),
                            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                            ('LEFTPADDING', (0, 0), (-1, -1), 6),
                        ]))
                        elements.append(info_table)
                        elements.append(Spacer(1, 0.3*inch))
                        
                        # Tabla de productos
                        elements.append(Paragraph("PRODUCTOS SOLICITADOS", subtitle_style))
                        products_data = [['#', 'Producto', 'Cantidad', 'Precio Unit.', 'Total']]
                        for idx, prod in enumerate(prods_result, 1):
                            products_data.append([
                                str(idx),
                                prod[0] or 'N/A',
                                str(float(prod[1] or 0)),
                                f"Bs. {float(prod[2] or 0):.2f}",
                                f"Bs. {float(prod[3] or 0):.2f}"
                            ])
                        
                        products_table = Table(products_data, colWidths=[0.4*inch, 3.5*inch, 0.8*inch, 1.0*inch, 1.0*inch])
                        products_table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('ALIGN', (1, 1), (1, -1), 'LEFT'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, 0), 10),
                            ('FONTSIZE', (0, 1), (-1, -1), 9),
                            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')]),
                        ]))
                        elements.append(products_table)
                        elements.append(Spacer(1, 0.2*inch))
                        
                        # Pie de p??gina
                        footer = Paragraph(
                            f"Documento generado el {datetime.now().strftime('%d/%m/%Y a las %H:%M')} - Sistema de Almac??n SEDH",
                            ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey, alignment=TA_CENTER)
                        )
                        elements.append(footer)
                        
                        doc.build(elements)
                        buffer.seek(0)
                        attachments.append((f"Requisicion_{cod_req}.pdf", buffer.read(), "application/pdf"))
                except Exception as pdf_err:
                    print(f"WARN: No se pudo generar PDF para adjuntar al solicitante: {pdf_err}")
                    import traceback
                    traceback.print_exc()
                    pass

                estado_solic, error_solic = send_email(
                    correo_dest,
                    asunto_solic,
                    cuerpo_text_solic,
                    body_html=cuerpo_html_solic,
                    attachments=attachments,
                    inline_images=inline_images,
                )
                registrar_email_log(correo_dest, asunto_solic, cuerpo_text_solic, estado_solic, error_solic, result.idrequisicion, db)
                if estado_solic != "enviado":
                    print(f"WARN: Error al enviar confirmaci??n al solicitante {correo_dest}: {error_solic}")
            except Exception as correo_solic_err:
                print(f"WARN: Fallo al enviar correo al solicitante: {correo_solic_err}")

            db.commit()
        except Exception as _notif_err:
            # No bloquear la creaci??n por fallo al notificar; registrar y continuar
            try:
                db.rollback()
            except Exception:
                pass
            # Opcional: log en consola
            print(f"WARN: Fallo al crear notificaciones de requisici??n: {_notif_err}")

        return result
    except ValueError as e:
        import traceback
        print(f"ERROR ValueError: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=400, detail=str(e))
    except ProgrammingError as e:
        import traceback
        print(f"ERROR ProgrammingError: {str(e)}")
        print(traceback.format_exc())
        msg = str(getattr(e, "orig", e))
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {msg}")
    except SQLAlchemyError as e:
        import traceback
        print(f"ERROR SQLAlchemyError: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {str(e)}")
    except Exception as e:
        import traceback
        print(f"ERROR Exception: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")


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
        raise HTTPException(status_code=401, detail="No se encontr?? email del usuario autenticado")

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
    summary="Responder (aprobar/rechazar) una requisici??n de un subordinado",
    response_model=ResponderRequisicionOut,
)
async def api_responder_requisicion_jefe(
    body: ResponderRequisicionIn,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    email = (str(current_user.get("email") or current_user.get("sub") or "")).strip()
    if not email:
        raise HTTPException(status_code=401, detail="No se encontr?? email del usuario autenticado")

    try:
        result = responder_requisicion_jefe(db, body, email)
        
        # Registrar en auditor??a si la aprobaci??n fue exitosa
        try:
            if body.estado.upper() == "APROBADO":
                actualizar_timestamp_aprobacion_jefe(db, str(body.idRequisicion), str(current_user.get("id", "")))
                registrar_auditoria_requisicion(
                    db=db,
                    id_requisicion=str(body.idRequisicion),
                    tipo_accion="APROBADA_JEFE",
                    id_usuario_accion=str(current_user.get("id", "")),
                    nombre_usuario_accion=current_user.get("nombre", email),
                    descripcion_accion="Aprobada por jefe de departamento",
                    observaciones=body.comentario
                )
            elif body.estado.upper() == "RECHAZADO":
                actualizar_timestamp_rechazo(db, str(body.idRequisicion))
                registrar_auditoria_requisicion(
                    db=db,
                    id_requisicion=str(body.idRequisicion),
                    tipo_accion="RECHAZADA",
                    id_usuario_accion=str(current_user.get("id", "")),
                    nombre_usuario_accion=current_user.get("nombre", email),
                    descripcion_accion="Rechazada por jefe de departamento",
                    observaciones=f"Motivo: {body.comentario}"
                )
        except Exception as audit_error:
            print(f"Advertencia: Error al registrar auditor??a: {audit_error}")
        
        return result
    except ProgrammingError as e:
        db.rollback()
        msg = str(getattr(e, "orig", e))
        if "Usuario no autorizado" in msg or "no es Jefe Inmediato" in msg:
            raise HTTPException(status_code=401, detail="Usuario no autorizado: no es Jefe Inmediato")
        if "Estado inv??lido" in msg or "Comentario es obligatorio" in msg:
            raise HTTPException(status_code=400, detail=msg)
        print(f"ERROR ProgrammingError: {e}")
        print(f"ERROR msg: {msg}")
        raise HTTPException(status_code=500, detail=f"Error al responder la requisici??n: {msg}")
    except SQLAlchemyError as e:
        db.rollback()
        print(f"ERROR SQLAlchemyError: {e}")
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {str(e)}")
    except Exception as e:
        db.rollback()
        print(f"ERROR Exception: {e}")
        print(f"ERROR tipo: {type(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")

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
        raise HTTPException(status_code=401, detail="No se encontr?? email del usuario autenticado")

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
    summary="Gerente Administrativo responde (aprobar/rechazar) una requisici??n",
    response_model=ResponderRequisicionOut,
)
async def api_responder_requisicion_gerente(
    body: ResponderRequisicionGerenteIn,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    email = (str(current_user.get("email") or current_user.get("sub") or "")).strip()
    if not email:
        raise HTTPException(status_code=401, detail="No se encontr?? email del usuario autenticado")

    try:
        result = responder_requisicion_gerente(db, body, email)
        
        # Registrar en auditor??a si la aprobaci??n fue exitosa
        try:
            if body.estado.upper() == "APROBADO":
                actualizar_timestamp_aprobacion_jefe(db, str(body.idRequisicion), str(current_user.get("id", "")))
                registrar_auditoria_requisicion(
                    db=db,
                    id_requisicion=str(body.idRequisicion),
                    tipo_accion="APROBADA_GERENTE",
                    id_usuario_accion=str(current_user.get("id", "")),
                    nombre_usuario_accion=current_user.get("nombre", email),
                    descripcion_accion="Aprobada por Gerente Administrativo",
                    observaciones=body.comentario
                )
            elif body.estado.upper() == "RECHAZADO":
                actualizar_timestamp_rechazo(db, str(body.idRequisicion))
                registrar_auditoria_requisicion(
                    db=db,
                    id_requisicion=str(body.idRequisicion),
                    tipo_accion="RECHAZADA",
                    id_usuario_accion=str(current_user.get("id", "")),
                    nombre_usuario_accion=current_user.get("nombre", email),
                    descripcion_accion="Rechazada por Gerente Administrativo",
                    observaciones=f"Motivo: {body.comentario}"
                )
        except Exception as audit_error:
            print(f"Advertencia: Error al registrar auditor??a: {audit_error}")
        
        return result
    except ProgrammingError as e:
        db.rollback()
        msg = str(getattr(e, "orig", e))
        if "Usuario no autorizado" in msg or "no es Gerente Administrativo" in msg:
            raise HTTPException(status_code=401, detail="Usuario no autorizado: no es Gerente Administrativo")
        if "Estado inv??lido" in msg or "Comentario es obligatorio" in msg:
            raise HTTPException(status_code=400, detail=msg)
        raise HTTPException(status_code=500, detail="Error al responder la requisici??n")
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")

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
        raise HTTPException(status_code=401, detail="No se encontr?? email del usuario autenticado")

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
    summary="Jefe de Materiales responde (aprobar/rechazar) una requisici??n",
    response_model=ResponderRequisicionOut,
)
async def api_responder_requisicion_jefe_materiales(
    body: ResponderRequisicionGerenteIn,  # reutiliza el esquema del gerente
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    email = (str(current_user.get("email") or current_user.get("sub") or "")).strip()
    if not email:
        raise HTTPException(status_code=401, detail="No se encontr?? email del usuario autenticado")

    try:
        result = responder_requisicion_jefe_materiales(db, body, email)
        
        # Registrar en auditor??a si la aprobaci??n fue exitosa
        try:
            if body.estado.upper() == "APROBADO":
                actualizar_timestamp_aprobacion_almacen(db, str(body.idRequisicion), str(current_user.get("id", "")))
                registrar_auditoria_requisicion(
                    db=db,
                    id_requisicion=str(body.idRequisicion),
                    tipo_accion="APROBADA_JEFE_MATERIALES",
                    id_usuario_accion=str(current_user.get("id", "")),
                    nombre_usuario_accion=current_user.get("nombre", email),
                    descripcion_accion="Aprobada por Jefe de Materiales",
                    observaciones=body.comentario
                )
            elif body.estado.upper() == "RECHAZADO":
                actualizar_timestamp_rechazo(db, str(body.idRequisicion))
                registrar_auditoria_requisicion(
                    db=db,
                    id_requisicion=str(body.idRequisicion),
                    tipo_accion="RECHAZADA",
                    id_usuario_accion=str(current_user.get("id", "")),
                    nombre_usuario_accion=current_user.get("nombre", email),
                    descripcion_accion="Rechazada por Jefe de Materiales",
                    observaciones=f"Motivo: {body.comentario}"
                )
        except Exception as audit_error:
            print(f"Advertencia: Error al registrar auditor??a: {audit_error}")
        
        return result
    except ProgrammingError as e:
        db.rollback()
        msg = str(getattr(e, "orig", e))
        if "Usuario no autorizado" in msg or "no es Jefe de Materiales" in msg:
            raise HTTPException(status_code=401, detail="Usuario no autorizado: no es Jefe de Materiales")
        if "Estado inv??lido" in msg or "Comentario es obligatorio" in msg or "no puede aumentar la cantidad" in msg:
            raise HTTPException(status_code=400, detail=msg)
        raise HTTPException(status_code=500, detail="Error al responder la requisici??n (jefe de materiales)")
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")

# EMPLEADOS ALMACEN
@router.get(
    "/pendientes/almacen",
    summary="Listar requisiciones pendientes del Empleado de Almac??n",
    response_model=list[RequisicionPendienteGerenteOut],
)
async def api_requisiciones_pendientes_almacen(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    email = (str(current_user.get("email") or current_user.get("sub") or "")).strip()
    if not email:
        raise HTTPException(status_code=401, detail="No se encontr?? email del usuario autenticado")

    try:
        return requisiciones_pendientes_almacen(db, email)
    except ProgrammingError as e:
        msg = str(getattr(e, "orig", e))
        if "Usuario no autorizado" in msg or "no es Empleado de Almac??n" in msg:
            raise HTTPException(status_code=401, detail="Usuario no autorizado: no es Empleado de Almac??n")
        raise HTTPException(status_code=500, detail="Error al consultar requisiciones pendientes (almac??n)")
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Error de base de datos")
    except Exception:
        raise HTTPException(status_code=500, detail="Error inesperado")


# ====================================
# GENERAR PDF DE REQUISICI??N
# ====================================
@router.get("/{id_requisicion}/pdf", summary="Generar PDF imprimible de una requisici??n")
async def api_generar_pdf_requisicion(
    id_requisicion: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    from_: str | None = None,
    to: str | None = None,
):
    """
    Genera un PDF con el formato oficial de la requisici??n, incluyendo:
    - Informaci??n general de la requisici??n
    - Tabla de productos solicitados
    - Hist??rico de aprobaciones
    - Espacios para firmas
    
    Acepta tanto UUID (idrequisicion) como c??digo (codrequisicion)
    """
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from datetime import datetime
    import re
    import uuid
    
    try:
        # Detectar si es UUID o c??digo
        actual_id = id_requisicion
        try:
            uuid.UUID(id_requisicion)
            # Es un UUID v??lido
        except ValueError:
            # No es UUID, buscar por c??digo
            q_id = text("SELECT idrequisicion FROM requisiciones.requisiciones WHERE codrequisicion = :cod LIMIT 1")
            id_row = db.execute(q_id, {"cod": id_requisicion}).first()
            if not id_row:
                raise HTTPException(status_code=404, detail=f"Requisici??n con c??digo '{id_requisicion}' no encontrada")
            actual_id = str(id_row[0])
        
        # Consulta completa para obtener toda la informaci??n de la requisici??n
        query_requisicion = text("""
            SELECT 
                r.idrequisicion,
                r.codrequisicion,
                r.fecsolicitud,
                r.estgeneral,
                r.gastotaldelpedido,
                r.obsempleado,
                r.obsalmacen,
                r.motrechazo,
                r.reqentregadopor,
                r.reqrecibidopor,
                r.creadopor AS email_solicitante,
                r.nomempleado AS nombre_empleado,
                '' AS apellido_empleado,
                d.nomdependencia AS dependencia,
                d.siglas AS sigla_dependencia,
                -- Productos
                (
                    SELECT json_agg(
                        json_build_object(
                            'nombre', p.nomproducto,
                            'codigo', p.codobjetounico,
                            'cantidad', dr.cantsolicitada,
                            'precio_unitario', dr.gasunitario,
                            'precio_total', dr.gastotalproducto,
                            'factura', COALESCE(p.facturas, ''),
                            'orden_compra', COALESCE(p.ordenescompra, '')
                        ) ORDER BY dr.iddetallerequisicion
                    )
                    FROM requisiciones.detalle_requisicion dr
                    JOIN productos.productos p ON dr.idproducto = p.idproducto
                    WHERE dr.idrequisicion = r.idrequisicion
                ) AS productos,
                -- Aprobaciones
                (
                    SELECT json_agg(
                        json_build_object(
                            'rol', a.rol,
                            'observaciones', a.comentario,
                            'fecha', a.fecaprobacion,
                            'nombre_aprobador', ea.nombre
                        ) ORDER BY a.fecaprobacion
                    )
                    FROM requisiciones.aprobaciones a
                    LEFT JOIN usuarios.empleados ea ON a.emailinstitucional = ea.emailinstitucional
                    WHERE a.idrequisicion = r.idrequisicion
                ) AS aprobaciones
            FROM requisiciones.requisiciones r
            LEFT JOIN usuarios.dependencias d ON r.iddependencia = d.iddependencia
            WHERE r.idrequisicion = :id_requisicion
        """)
        
        result = db.execute(query_requisicion, {"id_requisicion": actual_id}).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Requisici??n no encontrada")
        
        # Crear PDF en memoria
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=0.75*inch, leftMargin=0.75*inch, 
                               topMargin=1*inch, bottomMargin=0.75*inch)
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], 
                                     fontSize=16, textColor=colors.HexColor('#1a365d'),
                                     spaceAfter=12, alignment=TA_CENTER, fontName='Helvetica-Bold')
        
        subtitle_style = ParagraphStyle('CustomSubtitle', parent=styles['Heading2'],
                                       fontSize=12, textColor=colors.HexColor('#2d3748'),
                                       spaceAfter=10, fontName='Helvetica-Bold')
        
        normal_style = ParagraphStyle('CustomNormal', parent=styles['Normal'],
                                     fontSize=10, fontName='Helvetica')
        
        # Contenido del PDF
        elements = []
        
        # Encabezado
        title = Paragraph("SISTEMA DE ALMAC??N - SEDH", title_style)
        subtitle = Paragraph(f"REQUISICI??N DE MATERIALES", subtitle_style)
        elements.append(title)
        elements.append(subtitle)
        elements.append(Spacer(1, 0.3*inch))
        
        # Informaci??n general
        info_data = [
            ['C??digo:', result.codrequisicion, 'Fecha Solicitud:', result.fecsolicitud.strftime('%d/%m/%Y')],
            ['Solicitante:', f"{result.nombre_empleado} {result.apellido_empleado}", 'Estado:', result.estgeneral],
            ['Dependencia:', f"{result.dependencia} ({result.sigla_dependencia})", 'Gasto Total:', f"Bs. {float(result.gastotaldelpedido or 0):.2f}"],
            ['Correo Institucional:', (result.email_solicitante or 'N/A'), '', '']
        ]
        
        info_table = Table(info_data, colWidths=[1.2*inch, 2.5*inch, 1.3*inch, 1.5*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e2e8f0')),
            ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#e2e8f0')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 0.3*inch))

        # Programas asociados (removido en rollback)
        
        # Tabla de productos
        products_title = Paragraph("PRODUCTOS SOLICITADOS", subtitle_style)
        elements.append(products_title)
        
        productos = result.productos or []
        products_data = [['#', 'C??digo', 'Producto', 'Cantidad', 'P. Unitario', 'P. Total', 'Factura', 'Orden Compra']]
        
        for idx, prod in enumerate(productos, 1):
            products_data.append([
                str(idx),
                prod['codigo'] or 'N/A',
                prod['nombre'],
                str(prod['cantidad']),
                f"Bs. {float(prod['precio_unitario'] or 0):.2f}",
                f"Bs. {float(prod['precio_total'] or 0):.2f}",
                (prod.get('factura') or ''),
                (prod.get('orden_compra') or '')
            ])
        
        products_table = Table(products_data, colWidths=[0.4*inch, 1*inch, 2.4*inch, 0.8*inch, 1*inch, 1*inch, 1.1*inch, 1.1*inch])
        products_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (2, 1), (2, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')]),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(products_table)
        elements.append(Spacer(1, 0.3*inch))

        # Comparativo de totales (calculado vs registro)
        try:
            total_calculado = sum(float(p.get('precio_total') or 0) for p in (result.productos or []))
        except Exception:
            total_calculado = 0.0
        comp_title = Paragraph("TOTAL DEL PEDIDO", subtitle_style)
        elements.append(comp_title)
        comp_data = [
            ['Total Calculado (suma productos)', f"Bs. {total_calculado:.2f}"],
            ['Gasto Total Registrado', f"Bs. {float(result.gastotaldelpedido or 0):.2f}"]
        ]
        comp_table = Table(comp_data, colWidths=[3.0*inch, 4.0*inch])
        comp_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e2e8f0')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(comp_table)
        elements.append(Spacer(1, 0.3*inch))

        # Observaciones y log??stica
        obs_title = Paragraph("OBSERVACIONES Y LOG??STICA", subtitle_style)
        elements.append(obs_title)
        obs_data = [
            ['Observaciones Empleado', (result.obsempleado or '-')],
            ['Observaciones Almac??n', (result.obsalmacen or '-')],
            ['Entregado Por', (result.reqentregadopor or '-')],
            ['Recibido Por', (result.reqrecibidopor or '-')]
        ]
        if str(result.estgeneral or '').upper() == 'RECHAZADO':
            obs_data.append(['Motivo de Rechazo', (result.motrechazo or '-')])
        obs_table = Table(obs_data, colWidths=[2.2*inch, 4.8*inch])
        obs_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e2e8f0')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(obs_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Hist??rico de aprobaciones
        approvals_title = Paragraph("HIST??RICO DE APROBACIONES", subtitle_style)
        elements.append(approvals_title)
        
        aprobaciones = result.aprobaciones or []
        approvals_data = [['Rol', 'Aprobador', 'Fecha', 'Observaciones']]
        
        rol_nombres = {
            'JefInmediato': 'Jefe Inmediato',
            'GerAdmon': 'Gerente Administrativo',
            'JefSerMat': 'Jefe de Servicios y Materiales',
            'EmpAlmacen': 'Empleado de Almac??n'
        }
        
        for aprob in aprobaciones:
            # Formatear fecha correctamente
            fecha_str = 'N/A'
            if aprob['fecha']:
                try:
                    if isinstance(aprob['fecha'], str):
                        # Si es string, convertir a fecha
                        fecha_obj = datetime.fromisoformat(str(aprob['fecha']).split('T')[0])
                    else:
                        # Si es date object
                        fecha_obj = aprob['fecha']
                    fecha_str = fecha_obj.strftime('%d/%m/%Y')
                except:
                    fecha_str = str(aprob['fecha'])
            
            approvals_data.append([
                rol_nombres.get(aprob['rol'], aprob['rol']),
                aprob['nombre_aprobador'] or 'N/A',
                fecha_str,
                aprob['observaciones'] or '-'
            ])
        
        if len(aprobaciones) == 0:
            approvals_data.append(['Sin aprobaciones registradas', '', '', ''])
        
        approvals_table = Table(approvals_data, colWidths=[1.5*inch, 1.8*inch, 1.3*inch, 2.4*inch])
        approvals_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')]),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(approvals_table)
        elements.append(Spacer(1, 0.3*inch))

        # Timeline de eventos (desde notificaciones)
        try:
            base_tl = """
                SELECT n.fechacreacion AS fecha, n.emailusuario AS usuario, n.mensaje AS mensaje
                FROM requisiciones.notificaciones n
                WHERE n.idrequisicion = :id_requisicion
            """
            filtros_tl = []
            params_tl = {"id_requisicion": result.idrequisicion}
            if from_:
                filtros_tl.append("n.fechacreacion::date >= :from")
                params_tl["from"] = from_
            if to:
                filtros_tl.append("n.fechacreacion::date <= :to")
                params_tl["to"] = to
            if filtros_tl:
                base_tl += " AND " + " AND ".join(filtros_tl)
            base_tl += " ORDER BY n.fechacreacion"
            query_timeline = text(base_tl)
            timeline_rows = db.execute(query_timeline, params_tl).fetchall()
        except Exception:
            timeline_rows = []

        timeline_title = Paragraph("TIMELINE DE EVENTOS", subtitle_style)
        elements.append(timeline_title)
        timeline_data = [['Fecha', 'Usuario', 'Evento']]
        for ev in timeline_rows:
            # Formatear fecha
            fecha_str = 'N/A'
            try:
                fecha_val = ev[0]
                if hasattr(fecha_val, 'strftime'):
                    fecha_str = fecha_val.strftime('%d/%m/%Y %H:%M')
                else:
                    fecha_str = str(fecha_val)
            except Exception:
                fecha_str = str(ev[0])

            usuario = ev[1] or ''
            mensaje = ev[2] or ''
            timeline_data.append([fecha_str, usuario, mensaje])

        if len(timeline_rows) == 0:
            timeline_data.append(['Sin eventos', '', ''])

        timeline_table = Table(timeline_data, colWidths=[1.6*inch, 2.0*inch, 3.6*inch])
        timeline_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')]),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(timeline_table)
        elements.append(Spacer(1, 0.3*inch))

        # Ajustes realizados (si existen en las observaciones de aprobaciones)
        ajustes_registros = []
        try:
            for aprob in (result.aprobaciones or []):
                obs = (aprob.get('observaciones') or '').strip()
                if not obs:
                    continue
                m = re.search(r"Ajustes\s+realizados:(.*)$", obs, re.IGNORECASE | re.DOTALL)
                if not m:
                    continue
                bloque = m.group(1)
                for linea in bloque.splitlines():
                    linea = linea.strip()
                    if not linea.startswith('-'):
                        continue
                    mm = re.match(r"-\s*(.+?)\s*\(([^)]+)\):\s*([0-9.,]+)\s*\u2192\s*([0-9.,]+)", linea)
                    if not mm:
                        # Intentar con flecha ASCII por compatibilidad
                        mm = re.match(r"-\s*(.+?)\s*\(([^)]+)\):\s*([0-9.,]+)\s*->\s*([0-9.,]+)", linea)
                    if mm:
                        producto = mm.group(1)
                        codigo = mm.group(2)
                        original = mm.group(3)
                        nuevo = mm.group(4)
                        ajustes_registros.append([
                            producto,
                            codigo,
                            original,
                            nuevo,
                            f"{rol_nombres.get(aprob.get('rol'), aprob.get('rol'))} - {aprob.get('nombre_aprobador') or 'N/A'}"
                        ])
        except Exception:
            ajustes_registros = ajustes_registros  # Si hay error de parseo, continuar sin bloquear

        if len(ajustes_registros) > 0:
            ajustes_title = Paragraph("AJUSTES REALIZADOS", subtitle_style)
            elements.append(ajustes_title)
            ajustes_data = [['Producto', 'C??digo', 'Original', 'Nuevo', 'Por']]
            ajustes_data.extend(ajustes_registros)

            ajustes_table = Table(ajustes_data, colWidths=[2.6*inch, 1.1*inch, 0.9*inch, 0.9*inch, 2.0*inch])
            ajustes_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')]),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(ajustes_table)
            elements.append(Spacer(1, 0.3*inch))

        elements.append(Spacer(1, 0.5*inch))
        
        # Espacios para firmas
        signatures_title = Paragraph("FIRMAS Y SELLOS", subtitle_style)
        elements.append(signatures_title)
        elements.append(Spacer(1, 0.2*inch))
        
        signatures_data = [
            ['Solicitante', 'Jefe Inmediato', 'Almac??n'],
            ['_____________________', '_____________________', '_____________________'],
            ['', '', ''],
            ['Fecha: ___/___/___', 'Fecha: ___/___/___', 'Fecha: ___/___/___']
        ]
        
        signatures_table = Table(signatures_data, colWidths=[2.3*inch, 2.3*inch, 2.3*inch])
        signatures_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
            ('TOPPADDING', (0, 2), (-1, 2), 15),
        ]))
        elements.append(signatures_table)
        
        # Pie de p??gina
        elements.append(Spacer(1, 0.3*inch))
        footer = Paragraph(
            f"Documento generado el {datetime.now().strftime('%d/%m/%Y a las %H:%M')} - Sistema de Almac??n SEDH",
            ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey, alignment=TA_CENTER)
        )
        elements.append(footer)
        
        # Construir PDF
        doc.build(elements)
        
        # Preparar respuesta
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=Requisicion_{result.codrequisicion}.pdf"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar PDF: {str(e)}")


# RESPONDER REQUISICION ALMACEN
@router.post(
    "/responder/almacen",
    summary="Empleado de Almac??n responde (aprobar/rechazar) una requisici??n",
    response_model=ResponderRequisicionOut,
)
async def api_responder_requisicion_almacen(
    body: ResponderRequisicionGerenteIn,  # reutiliza el esquema del gerente
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    email = (str(current_user.get("email") or current_user.get("sub") or "")).strip()
    if not email:
        raise HTTPException(status_code=401, detail="No se encontr?? email del usuario autenticado")

    try:
        result = responder_requisicion_almacen(db, body, email)
        
        # Registrar en auditor??a si la aprobaci??n fue exitosa
        try:
            if body.estado.upper() == "APROBADO":
                actualizar_timestamp_aprobacion_almacen(db, str(body.idRequisicion), str(current_user.get("id", "")))
                registrar_auditoria_requisicion(
                    db=db,
                    id_requisicion=str(body.idRequisicion),
                    tipo_accion="APROBADA_ALMACEN",
                    id_usuario_accion=str(current_user.get("id", "")),
                    nombre_usuario_accion=current_user.get("nombre", email),
                    descripcion_accion="Aprobada por Encargado de Almac??n",
                    observaciones=body.comentario
                )
            elif body.estado.upper() == "RECHAZADO":
                actualizar_timestamp_rechazo(db, str(body.idRequisicion))
                registrar_auditoria_requisicion(
                    db=db,
                    id_requisicion=str(body.idRequisicion),
                    tipo_accion="RECHAZADA",
                    id_usuario_accion=str(current_user.get("id", "")),
                    nombre_usuario_accion=current_user.get("nombre", email),
                    descripcion_accion="Rechazada por Encargado de Almac??n",
                    observaciones=f"Motivo: {body.comentario}"
                )
        except Exception as audit_error:
            print(f"Advertencia: Error al registrar auditor??a: {audit_error}")
        
        return result
    except ProgrammingError as e:
        db.rollback()
        msg = str(getattr(e, "orig", e))
        if "Usuario no autorizado" in msg or "no es Empleado de Almac??n" in msg:
            raise HTTPException(status_code=401, detail="Usuario no autorizado: no es Empleado de Almac??n")
        if "Estado inv??lido" in msg or "Comentario es obligatorio" in msg or "no puede aumentar la cantidad" in msg:
            raise HTTPException(status_code=400, detail=msg)
        raise HTTPException(status_code=500, detail="Error al responder la requisici??n (almac??n)")
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")


# ENDPOINT DE PRUEBA SIMPLE
@router.get("/test-todas", summary="Test endpoint para debug")
async def test_todas_requisiciones(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Endpoint de prueba simple para verificar conectividad"""
    try:
        # Prueba 1: Verificar conexi??n b??sica
        query = text("SELECT COUNT(*) as total FROM requisiciones.requisiciones")
        result = db.execute(query)
        count = result.fetchone()[0]
        
        return {
            "mensaje": "Endpoint funcionando correctamente",
            "total_requisiciones": count,
            "usuario": current_user.get("email", "desconocido")
        }
    except Exception as e:
        import traceback
        error_detail = f"Error en test: {str(e)}\n{traceback.format_exc()}"
        print(f"ERROR EN TEST: {error_detail}")
        raise HTTPException(status_code=500, detail=error_detail)

# ENDPOINT PARA REPORTE COMPLETO - VERSION MUY SIMPLE
@router.get("/todas", summary="Obtener todas las requisiciones para reporte completo")
async def api_todas_requisiciones(
    mes: int = None,
    anio: int = None,
    estado: str = None,
    dependencia: str = None,
    busqueda: str = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Endpoint para obtener todas las requisiciones con informaci??n completa
    para el sistema de reportes mejorado.
    
    Filtros opcionales:
    - mes: N??mero del mes (1-12)
    - anio: A??o (ej: 2025)
    - estado: Estado general (EN ESPERA, APROBADO, RECHAZADO)
    - dependencia: UUID de la dependencia
    - busqueda: Texto para buscar en c??digo de requisici??n o nombre de empleado
    """
    email = (str(current_user.get("email") or current_user.get("sub") or "")).strip()
    if not email:
        raise HTTPException(status_code=401, detail="No se encontr?? email del usuario autenticado")
    
    try:
        print("DEBUG: Iniciando endpoint /todas - Conectando con BD real")
        
        # Construir la consulta con filtros din??micos
        base_query = """
            SELECT 
                r.idrequisicion,
                r.codrequisicion,
                r.nomempleado,
                r.iddependencia,
                r.fecsolicitud,
                r.estgeneral,
                r.obsempleado,
                r.gastotaldelpedido,
                r.creadoen,
                r.creadopor,
                COALESCE(d.nomdependencia, 'Sin Dependencia') as nomdependencia,
                COALESCE(d.siglas, 'SIN') as siglas
            FROM requisiciones.requisiciones r
            LEFT JOIN usuarios.dependencias d ON r.iddependencia = d.iddependencia
            WHERE 1=1
        """
        
        # Construir filtros din??micos
        filtros = []
        parametros = {}
        
        if mes:
            filtros.append("EXTRACT(MONTH FROM r.fecsolicitud) = :mes")
            parametros['mes'] = mes
            
        if anio:
            filtros.append("EXTRACT(YEAR FROM r.fecsolicitud) = :anio")
            parametros['anio'] = anio
            
        if estado:
            filtros.append("r.estgeneral ILIKE :estado")
            parametros['estado'] = f"%{estado}%"
            
        if dependencia:
            try:
                from uuid import UUID
                # Validar que sea un UUID v??lido
                uuid_obj = UUID(dependencia)
                filtros.append("r.iddependencia = :dependencia")
                parametros['dependencia'] = uuid_obj
            except ValueError:
                print(f"DEBUG: Dependencia inv??lida: {dependencia}")
                # Si no es un UUID v??lido, ignorar el filtro
        
        if busqueda:
            # Buscar en c??digo de requisici??n o nombre de empleado
            filtros.append("(r.codrequisicion ILIKE :busqueda OR r.nomempleado ILIKE :busqueda)")
            parametros['busqueda'] = f"%{busqueda}%"
        
        # Agregar filtros a la consulta
        if filtros:
            base_query += " AND " + " AND ".join(filtros)
        
        base_query += " ORDER BY r.fecsolicitud DESC, r.codrequisicion DESC"
        
        query = text(base_query)
        result = db.execute(query, parametros)
        requisiciones_bd = result.fetchall()
        
        print(f"DEBUG: Aplicados filtros - mes: {mes}, anio: {anio}, estado: {estado}, dependencia: {dependencia}, busqueda: {busqueda}")
        print(f"DEBUG: Encontradas {len(requisiciones_bd)} requisiciones en BD")
        
        
        # Convertir los resultados a formato esperado por el frontend
        requisiciones = []
        for req in requisiciones_bd:
            id_requisicion = str(req[0])
            
            # Consultar productos para esta requisici??n
            productos_query = text("""
                SELECT 
                    dr.idproducto,
                    COALESCE(p.nomproducto, 'Producto sin nombre') as nomproducto,
                    COALESCE(dr.cantsolicitada, 0) as cantsolicitada,
                    COALESCE(dr.gasunitario, 0) as gasunitario,
                    COALESCE(dr.gastotalproducto, 0) as gastotal,
                    COALESCE(p.facturas, '') as facturas,
                    COALESCE(p.ordenescompra, '') as ordenescompra
                FROM requisiciones.detalle_requisicion dr
                LEFT JOIN productos.productos p ON dr.idproducto = p.idproducto
                WHERE dr.idrequisicion = :id_requisicion
                ORDER BY p.nomproducto
            """)
            
            productos_result = db.execute(productos_query, {"id_requisicion": req[0]})
            productos_bd = productos_result.fetchall()
            
            # Convertir productos a formato esperado
            productos = []
            for prod in productos_bd:
                producto_dict = {
                    "IdProducto": prod[0],
                    "NomProducto": prod[1],
                    "CantSolicitada": int(prod[2]) if prod[2] else 0,
                    "GasUnitario": float(prod[3]) if prod[3] else 0.0,
                    "GasTotal": float(prod[4]) if prod[4] else 0.0,
                    "NumFactura": prod[5] if prod[5] else "",
                    "OrdenCompra": prod[6] if prod[6] else ""
                }
                productos.append(producto_dict)
            
            requisicion_dict = {
                "IdRequisicion": id_requisicion,
                "CodRequisicion": req[1] or "N/A",
                "NomEmpleado": req[2] or "Sin Nombre",
                "CreadoPor": req[9] or "Sistema",
                "IdDependencia": str(req[3]) if req[3] else "N/A",
                "SiglasDependencia": req[11] or "SIN",
                "NomDependencia": req[10] or "Sin Dependencia",
                "FecSolicitud": str(req[4]) if req[4] else "N/A",
                "EstGeneral": req[5] or "SIN ESTADO",
                "ObsEmpleado": req[6] or "Sin observaciones",
                "GasTotalDelPedido": float(req[7]) if req[7] else 0.0,
                "TotalProductos": len(productos),
                "Productos": productos,
                "FlujoAprobacion": {
                    "JefeInmediato": "Pendiente" if req[5] == "EN ESPERA" else ("Aprobado" if req[5] == "APROBADO" else "Rechazado"),
                    "GerenteAdministrativo": "Pendiente" if req[5] == "EN ESPERA" else ("Aprobado" if req[5] == "APROBADO" else "Rechazado"),
                    "JefeServiciosMateriales": "Pendiente" if req[5] == "EN ESPERA" else ("Aprobado" if req[5] == "APROBADO" else "Rechazado"),
                    "Almacen": "Pendiente" if req[5] == "EN ESPERA" else ("Aprobado" if req[5] == "APROBADO" else "Rechazado")
                }
            }
            requisiciones.append(requisicion_dict)
        
        print(f"DEBUG: Retornando {len(requisiciones)} requisiciones reales de la BD")
        return requisiciones
        
        # C??DIGO DE RESPALDO - datos simulados (comentado)
        """
        requisiciones_simuladas = [
            {
                "IdRequisicion": "1",
                "CodRequisicion": "UIT-001-2025",
                "NomEmpleado": "Humberto Josue Zelaya Lagos",
                "CreadoPor": "humberto.zelaya@sedh.gob.hn",
                "IdDependencia": "1",
                "SiglasDependencia": "UIT",
                "NomDependencia": "Unidad de Inform??tica y Tecnolog??a",
                "FecSolicitud": "2025-11-15T09:30:00",
                "EstGeneral": "EN ESPERA",
                "ObsEmpleado": "Equipos de c??mputo para mejorar la infraestructura tecnol??gica",
                "GasTotalDelPedido": 1850.0,
                "TotalProductos": 3,
                "Productos": [
                    {
                        "IdProducto": 1,
                        "NomProducto": "Laptop Dell Inspiron 15 - Core i5",
                        "CantSolicitada": 1,
                        "GasUnitario": 950.0,
                        "GasTotal": 950.0
                    },
                    {
                        "IdProducto": 2,
                        "NomProducto": "Mouse Inal??mbrico Logitech MX Master", 
                        "CantSolicitada": 2,
                        "GasUnitario": 350.0,
                        "GasTotal": 700.0
                    },
                    {
                        "IdProducto": 3,
                        "NomProducto": "Teclado Mec??nico USB",
                        "CantSolicitada": 1,
                        "GasUnitario": 200.0,
                        "GasTotal": 200.0
                    }
                ],
                "FlujoAprobacion": {
                    "JefeInmediato": "Pendiente",
                    "GerenteAdministrativo": "Pendiente", 
                    "JefeServiciosMateriales": "Pendiente",
                    "Almacen": "Pendiente"
                }
            },
            {
                "IdRequisicion": "2",
                "CodRequisicion": "SEDH-002-2025",
                "NomEmpleado": "Juan Gabriel",
                "CreadoPor": "juan.gabriel@sedh.gob.hn",
                "IdDependencia": "2",
                "SiglasDependencia": "SEDH",
                "NomDependencia": "Secretar??a de Estado en los Derechos Humanos",
                "FecSolicitud": "2025-11-10T14:15:00",
                "EstGeneral": "APROBADO",
                "ObsEmpleado": "Material de oficina para actividades administrativas urgentes",
                "GasTotalDelPedido": 1900.0,
                "TotalProductos": 4,
                "Productos": [
                    {
                        "IdProducto": 4,
                        "NomProducto": "Impresora HP LaserJet Pro M404dn",
                        "CantSolicitada": 1,
                        "GasUnitario": 1200.0,
                        "GasTotal": 1200.0
                    },
                    {
                        "IdProducto": 5,
                        "NomProducto": "Papel Bond Carta 75g - Resma",
                        "CantSolicitada": 10,
                        "GasUnitario": 35.0,
                        "GasTotal": 350.0
                    },
                    {
                        "IdProducto": 6,
                        "NomProducto": "T??ner HP Original 59A",
                        "CantSolicitada": 2,
                        "GasUnitario": 175.0,
                        "GasTotal": 350.0
                    }
                ],
                "FlujoAprobacion": {
                    "JefeInmediato": "Aprobado",
                    "GerenteAdministrativo": "Aprobado",
                    "JefeServiciosMateriales": "Aprobado",
                    "Almacen": "Aprobado"
                }
            },
            {
                "IdRequisicion": "3",
                "CodRequisicion": "ADMIN-003-2025",
                "NomEmpleado": "Escarleth Yadira Nu??ez Ortiz",
                "CreadoPor": "escarleth.ortiz@sedh.gob.hn",
                "IdDependencia": "3",
                "SiglasDependencia": "ADMIN",
                "NomDependencia": "Administraci??n General",
                "FecSolicitud": "2025-11-18T11:45:00",
                "EstGeneral": "RECHAZADO",
                "ObsEmpleado": "Suministros para ??rea administrativa",
                "GasTotalDelPedido": 680.0,
                "TotalProductos": 2,
                "Productos": [
                    {
                        "IdProducto": 7,
                        "NomProducto": "Archivadores de Palanca Tama??o Oficio",
                        "CantSolicitada": 12,
                        "GasUnitario": 25.0,
                        "GasTotal": 300.0
                    },
                    {
                        "IdProducto": 8,
                        "NomProducto": "Calculadora Cient??fica Casio FX-570",
                        "CantSolicitada": 2,
                        "GasUnitario": 190.0,
                        "GasTotal": 380.0
                    }
                ],
                "FlujoAprobacion": {
                    "JefeInmediato": "Rechazado",
                    "GerenteAdministrativo": "No Procesado",
                    "JefeServiciosMateriales": "No Procesado",
                    "Almacen": "No Procesado"
                }
            }
        ]
        """
        # FIN DEL C??DIGO DE RESPALDO

        
    except Exception as e:
        import traceback
        error_detail = f"Error al obtener requisiciones: {str(e)}\n{traceback.format_exc()}"
        print(f"ERROR EN ENDPOINT /todas: {error_detail}")
        raise HTTPException(status_code=500, detail=f"Error al obtener requisiciones: {str(e)}")

# ====================================
# Endpoints por c??digo para Historial
# ====================================
@router.get("/{cod}/detalle", summary="Detalle de requisici??n por c??digo")
async def api_detalle_por_codigo(
    cod: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    cod = (cod or "").strip()
    if not cod:
        raise HTTPException(status_code=400, detail="C??digo de requisici??n es obligatorio")
    try:
        # Consulta con el mismo esquema que `/todas`
        q = text(
            """
            SELECT 
                r.idrequisicion,
                r.codrequisicion,
                r.nomempleado,
                r.iddependencia,
                r.fecsolicitud,
                r.estgeneral,
                r.obsempleado,
                r.gastotaldelpedido,
                r.creadoen,
                r.creadopor,
                COALESCE(d.nomdependencia, 'Sin Dependencia') as nomdependencia,
                COALESCE(d.siglas, 'SIN') as siglas
            FROM requisiciones.requisiciones r
            LEFT JOIN usuarios.dependencias d ON r.iddependencia = d.iddependencia
            WHERE r.codrequisicion = :cod
            LIMIT 1
            """
        )
        req = db.execute(q, {"cod": cod}).fetchone()
        if not req:
            raise HTTPException(status_code=404, detail="Requisici??n no encontrada")

        # Productos
        productos_q = text(
            """
            SELECT 
                dr.idproducto,
                COALESCE(p.nomproducto, 'Producto sin nombre') as nomproducto,
                COALESCE(dr.cantsolicitada, 0) as cantsolicitada,
                COALESCE(dr.gasunitario, 0) as gasunitario,
                COALESCE(dr.gastotalproducto, 0) as gastotal
            FROM requisiciones.detalle_requisicion dr
            LEFT JOIN productos.productos p ON dr.idproducto = p.idproducto
            WHERE dr.idrequisicion = :id
            ORDER BY p.nomproducto
            """
        )
        prod_rows = db.execute(productos_q, {"id": req[0]}).fetchall()
        productos = [
            {
                "nombre": r[1],
                "cantidad": int(r[2]) if r[2] else 0,
                "estado": "",
                "precio_unitario": float(r[3]) if r[3] else 0.0,
                "precio_total": float(r[4]) if r[4] else 0.0,
            }
            for r in prod_rows
        ]

        return {
            "codigo": req[1],
            "fecha": str(req[4]) if req[4] else None,
            "estado": req[5],
            "total": float(req[7]) if req[7] else 0.0,
            "observaciones": req[6] or None,
            "solicitante": {
                "nombre": req[2],
                "dependencia": req[10],
                "sigla": req[11],
                "email": req[9] or None,
            },
            "productos": productos
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error consultando detalle: {str(e)}")


@router.get("/{cod}/aprobaciones", summary="Aprobaciones de requisici??n por c??digo")
async def api_aprobaciones_por_codigo(
    cod: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        q_id = text("SELECT idrequisicion FROM requisiciones.requisiciones WHERE codrequisicion = :cod LIMIT 1")
        id_row = db.execute(q_id, {"cod": cod}).first()
        if not id_row:
            raise HTTPException(status_code=404, detail="Requisici??n no encontrada")
        idreq = id_row[0]
        q = text(
            """
            SELECT 
                a.fecaprobacion AS fecha,
                a.estadoaprobacion AS estado,
                a.rol AS rol,
                COALESCE(ea.nombre, '') AS aprobador,
                COALESCE(a.comentario, '') AS observaciones
            FROM requisiciones.aprobaciones a
            LEFT JOIN usuarios.empleados ea ON a.emailinstitucional = ea.emailinstitucional
            WHERE a.idrequisicion = :id
            ORDER BY a.fecaprobacion
            """
        )
        rows = db.execute(q, {"id": idreq}).mappings().all()
        return rows
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error consultando aprobaciones: {str(e)}")


@router.get("/{cod}/historial", summary="Historial de eventos por c??digo")
async def api_historial_por_codigo(
    cod: str,
    from_: str = None,
    to: str = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        q_id = text("SELECT idrequisicion FROM requisiciones.requisiciones WHERE codrequisicion = :cod LIMIT 1")
        id_row = db.execute(q_id, {"cod": cod}).first()
        if not id_row:
            raise HTTPException(status_code=404, detail="Requisici??n no encontrada")
        idreq = id_row[0]
        base = """
            SELECT 
                n.fechacreacion AS fecha,
                n.emailusuario AS usuario,
                n.mensaje AS mensaje
            FROM requisiciones.notificaciones n
            WHERE n.idrequisicion = :id
        """
        filtros = []
        params = {"id": idreq}
        # Filtrar por rango si vienen par??metros (YYYY-MM-DD)
        if from_:
            filtros.append("n.fechacreacion::date >= :from")
            params["from"] = from_
        if to:
            filtros.append("n.fechacreacion::date <= :to")
            params["to"] = to
        if filtros:
            base += " AND " + " AND ".join(filtros)
        base += " ORDER BY n.fechacreacion"
        rows = db.execute(text(base), params).mappings().all()
        return rows
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error consultando historial: {str(e)}")


@router.get("/{cod}/pdf", summary="Generar PDF por c??digo")
async def api_pdf_por_codigo(
    cod: str,
    from_: str = None,
    to: str = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        q_id = text("SELECT idrequisicion FROM requisiciones.requisiciones WHERE codrequisicion = :cod LIMIT 1")
        id_row = db.execute(q_id, {"cod": cod}).first()
        if not id_row:
            raise HTTPException(status_code=404, detail="Requisici??n no encontrada")
        idreq = id_row[0]
        # Generar PDF aplicando opcionalmente el rango de fechas en el timeline
        return await api_generar_pdf_requisicion(str(idreq), db, current_user, from_=from_, to=to)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando PDF: {str(e)}")


# ===== ENDPOINTS DE AUDITOR??A Y TIEMPOS =====

@router.get("/auditoria/timeline/{id_requisicion}", summary="Timeline de auditor??a de una requisici??n")
async def obtener_timeline(
    id_requisicion: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Obtiene el timeline completo de una requisici??n con todos los eventos registrados
    
    Eventos: CREADA, ENVIADA, APROBADA_JEFE, APROBADA_ALMACEN, RECHAZADA, ENTREGADA
    """
    try:
        from app.repositories.requisiciones import obtener_timeline_requisicion
        
        timeline = obtener_timeline_requisicion(db, id_requisicion)
        
        if not timeline:
            raise HTTPException(status_code=404, detail="No hay eventos registrados para esta requisici??n")
        
        return {
            "id_requisicion": id_requisicion,
            "total_eventos": len(timeline),
            "eventos": timeline
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo timeline: {str(e)}")


@router.get("/auditoria/tiempos/{id_requisicion}", summary="C??lculo de tiempos entre etapas")
async def obtener_tiempos(
    id_requisicion: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Calcula los tiempos transcurridos entre cada etapa de la requisici??n.
    
    Retorna:
    - horas_creacion_a_envio: Horas desde creaci??n hasta env??o
    - horas_envio_a_jefe: Horas desde env??o hasta aprobaci??n del jefe
    - horas_jefe_a_almacen: Horas desde aprobaci??n jefe hasta aprobaci??n almac??n
    - horas_almacen_a_entrega: Horas desde aprobaci??n almac??n hasta entrega
    - dias_totales: D??as totales del proceso
    """
    try:
        from app.repositories.requisiciones import obtener_tiempos_requisicion
        
        tiempos = obtener_tiempos_requisicion(db, id_requisicion)
        
        if not tiempos:
            raise HTTPException(status_code=404, detail="Requisici??n no encontrada")
        
        # Redondear tiempos a 2 decimales
        for key in ['horas_creacion_a_envio', 'horas_envio_a_jefe', 'horas_jefe_a_almacen', 
                    'horas_almacen_a_entrega', 'dias_totales']:
            if tiempos.get(key):
                tiempos[key] = round(tiempos[key], 2)
        
        return tiempos
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculando tiempos: {str(e)}")


@router.post("/auditoria/registrar/{id_requisicion}", summary="Registrar evento de auditor??a")
async def registrar_evento_auditoria(
    id_requisicion: str,
    tipo_accion: str,
    descripcion: str = None,
    observaciones: str = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Registra un evento manual en la auditor??a de la requisici??n.
    
    Tipos de acci??n v??lidos: CREADA, ENVIADA, APROBADA_JEFE, APROBADA_ALMACEN, RECHAZADA, ENTREGADA
    """
    try:
        from app.repositories.requisiciones import registrar_auditoria_requisicion
        
        tipos_validos = ["CREADA", "ENVIADA", "APROBADA_JEFE", "APROBADA_ALMACEN", "RECHAZADA", "ENTREGADA"]
        
        if tipo_accion not in tipos_validos:
            raise HTTPException(
                status_code=400, 
                detail=f"Tipo de acci??n inv??lido. Debe ser uno de: {', '.join(tipos_validos)}"
            )
        
        resultado = registrar_auditoria_requisicion(
            db=db,
            id_requisicion=id_requisicion,
            tipo_accion=tipo_accion,
            id_usuario_accion=current_user.get("id"),
            nombre_usuario_accion=current_user.get("nombre", "Usuario desconocido"),
            descripcion_accion=descripcion,
            observaciones=observaciones
        )
        
        if not resultado:
            raise HTTPException(status_code=500, detail="Error registrando auditor??a")
        
        return {
            "success": True,
            "message": f"Evento {tipo_accion} registrado correctamente",
            "id_requisicion": id_requisicion
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error registrando auditor??a: {str(e)}")
