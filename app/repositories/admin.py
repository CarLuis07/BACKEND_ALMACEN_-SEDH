"""
Funciones administrativas para gestión de accesos, empleados, roles y dependencias
Solo disponibles para usuarios con rol 'Administrador'
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from uuid import UUID, uuid4
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)

def verificar_es_administrador(db: Session, email: str) -> bool:
    """
    Verifica si un usuario tiene rol de Administrador
    """
    try:
        resultado = db.execute(
            text("""
                SELECT r.nomrol 
                FROM acceso.empleados_roles er
                JOIN acceso.roles r ON r.idrol = er.idrol
                WHERE LOWER(TRIM(er.emailinstitucional)) = LOWER(TRIM(:email))
                AND COALESCE(er.actlaboralmente, FALSE) = TRUE
            """),
            {"email": email}
        ).mappings().first()
        
        return resultado and resultado["nomrol"] == "Administrador"
    except Exception as e:
        logger.error(f"Error verificando administrador: {e}")
        return False

# --- GESTIÓN DE EMPLEADOS ---
def listar_empleados(db: Session) -> List[Dict[str, Any]]:
    """Lista todos los empleados con su información completa"""
    try:
        resultados = db.execute(
            text("""
                SELECT 
                    e.emailinstitucional,
                    e.nombre as nombres,
                    '' as apellidos,
                    e.dni,
                    er.actlaboralmente,
                    er.ultimologin,
                    er.idrol,
                    r.nomrol,
                    e.iddependencia,
                    d.nomdependencia
                FROM usuarios.empleados e
                LEFT JOIN acceso.empleados_roles er ON er.emailinstitucional = e.emailinstitucional
                LEFT JOIN acceso.roles r ON r.idrol = er.idrol
                LEFT JOIN usuarios.dependencias d ON d.iddependencia = e.iddependencia
                ORDER BY e.nombre
            """)
        ).mappings().all()
        
        return [dict(row) for row in resultados]
    except Exception as e:
        logger.error(f"Error listando empleados: {e}")
        raise

def obtener_empleado(db: Session, email: str) -> Optional[Dict[str, Any]]:
    """Obtiene información de un empleado específico"""
    try:
        resultado = db.execute(
            text("""
                SELECT
                    er.emailinstitucional,
                    e.nombre as nombres,
                    '' as apellidos,
                    e.dni,
                    er.actlaboralmente,
                    er.ultimologin,
                    er.idrol,
                    r.nomrol,
                    e.iddependencia,
                    d.nomdependencia
                FROM acceso.empleados_roles er
                LEFT JOIN acceso.roles r ON r.idrol = er.idrol
                LEFT JOIN usuarios.empleados e ON e.emailinstitucional = er.emailinstitucional
                LEFT JOIN usuarios.dependencias d ON d.iddependencia = e.iddependencia
                WHERE LOWER(TRIM(er.emailinstitucional)) = LOWER(TRIM(:email))
            """),
            {"email": email}
        ).mappings().first()
        
        return dict(resultado) if resultado else None
    except Exception as e:
        logger.error(f"Error obteniendo empleado: {e}")
        raise

def crear_empleado(db: Session, datos: Dict[str, Any]) -> Dict[str, Any]:
    """Crea un nuevo empleado"""
    try:
        # Verificar si el email ya existe
        existe = db.execute(
            text("SELECT 1 FROM acceso.empleados_roles WHERE LOWER(TRIM(emailinstitucional)) = LOWER(TRIM(:email))"),
            {"email": datos["emailinstitucional"]}
        ).first()
        
        if existe:
            raise ValueError("Ya existe un empleado con este email")
        
        # Insertar nuevo empleado
        db.execute(
            text("""
                INSERT INTO acceso.empleados_roles 
                (emailinstitucional, nombres, apellidos, dni, contrasena, idrol, iddependencia, actlaboralmente)
                VALUES (:email, :nombres, :apellidos, :dni, :contrasena, :idrol, :iddependencia, :actlaboralmente)
            """),
            datos
        )
        db.commit()
        
        return {"mensaje": "Empleado creado exitosamente", "email": datos["emailinstitucional"]}
    except Exception as e:
        db.rollback()
        logger.error(f"Error creando empleado: {e}")
        raise

def actualizar_empleado(db: Session, email: str, datos: Dict[str, Any]) -> Dict[str, Any]:
    """Actualiza un empleado existente"""
    try:
        # Construir la consulta dinámicamente
        campos = []
        parametros = {"email": email}
        
        for campo, valor in datos.items():
            if valor is not None:
                campos.append(f"{campo} = :{campo}")
                parametros[campo] = valor
        
        if not campos:
            raise ValueError("No hay datos para actualizar")
        
        consulta = f"""
            UPDATE acceso.empleados_roles 
            SET {', '.join(campos)}
            WHERE LOWER(TRIM(emailinstitucional)) = LOWER(TRIM(:email))
        """
        
        resultado = db.execute(text(consulta), parametros)
        
        if resultado.rowcount == 0:
            raise ValueError("Empleado no encontrado")
        
        db.commit()
        return {"mensaje": "Empleado actualizado exitosamente", "email": email}
    except Exception as e:
        db.rollback()
        logger.error(f"Error actualizando empleado: {e}")
        raise

def cambiar_estado_empleado(db: Session, email: str, activo: bool) -> Dict[str, Any]:
    """Activa o desactiva un empleado"""
    try:
        resultado = db.execute(
            text("""
                UPDATE acceso.empleados_roles 
                SET actlaboralmente = :activo
                WHERE LOWER(TRIM(emailinstitucional)) = LOWER(TRIM(:email))
            """),
            {"email": email, "activo": activo}
        )
        
        if resultado.rowcount == 0:
            raise ValueError("Empleado no encontrado")
        
        db.commit()
        estado = "activado" if activo else "desactivado"
        return {"mensaje": f"Empleado {estado} exitosamente", "email": email}
    except Exception as e:
        db.rollback()
        logger.error(f"Error cambiando estado empleado: {e}")
        raise

# --- GESTIÓN DE ROLES ---
def listar_roles(db: Session) -> List[Dict[str, Any]]:
    """Lista todos los roles disponibles"""
    try:
        resultados = db.execute(
            text("SELECT idrol, nomrol FROM acceso.roles ORDER BY nomrol")
        ).mappings().all()
        
        return [dict(row) for row in resultados]
    except Exception as e:
        logger.error(f"Error listando roles: {e}")
        raise

def crear_rol(db: Session, nombre_rol: str) -> Dict[str, Any]:
    """Crea un nuevo rol"""
    try:
        # Verificar si el rol ya existe
        existe = db.execute(
            text("SELECT 1 FROM acceso.roles WHERE LOWER(TRIM(nomrol)) = LOWER(TRIM(:nombre))"),
            {"nombre": nombre_rol}
        ).first()
        
        if existe:
            raise ValueError("Ya existe un rol con este nombre")
        
        nuevo_id = str(uuid4())
        db.execute(
            text("INSERT INTO acceso.roles (idrol, nomrol) VALUES (:id, :nombre)"),
            {"id": nuevo_id, "nombre": nombre_rol}
        )
        db.commit()
        
        return {"mensaje": "Rol creado exitosamente", "idrol": nuevo_id, "nombre": nombre_rol}
    except Exception as e:
        db.rollback()
        logger.error(f"Error creando rol: {e}")
        raise

def actualizar_rol(db: Session, idrol: UUID, nuevo_nombre: str) -> Dict[str, Any]:
    """Actualiza el nombre de un rol"""
    try:
        resultado = db.execute(
            text("UPDATE acceso.roles SET nomrol = :nombre WHERE idrol = :id"),
            {"id": str(idrol), "nombre": nuevo_nombre}
        )
        
        if resultado.rowcount == 0:
            raise ValueError("Rol no encontrado")
        
        db.commit()
        return {"mensaje": "Rol actualizado exitosamente", "idrol": str(idrol)}
    except Exception as e:
        db.rollback()
        logger.error(f"Error actualizando rol: {e}")
        raise

def asignar_rol_empleado(db: Session, email: str, idrol: UUID) -> Dict[str, Any]:
    """Asigna un rol a un empleado"""
    try:
        # Verificar que el empleado existe
        empleado = db.execute(
            text("SELECT 1 FROM acceso.empleados_roles WHERE LOWER(TRIM(emailinstitucional)) = LOWER(TRIM(:email))"),
            {"email": email}
        ).first()
        
        if not empleado:
            raise ValueError("Empleado no encontrado")
        
        # Verificar que el rol existe
        rol = db.execute(
            text("SELECT nomrol FROM acceso.roles WHERE idrol = :id"),
            {"id": str(idrol)}
        ).mappings().first()
        
        if not rol:
            raise ValueError("Rol no encontrado")
        
        # Actualizar el rol del empleado
        db.execute(
            text("UPDATE acceso.empleados_roles SET idrol = :idrol WHERE LOWER(TRIM(emailinstitucional)) = LOWER(TRIM(:email))"),
            {"email": email, "idrol": str(idrol)}
        )
        db.commit()
        
        return {"mensaje": f"Rol '{rol['nomrol']}' asignado exitosamente a {email}", "email": email}
    except Exception as e:
        db.rollback()
        logger.error(f"Error asignando rol: {e}")
        raise

# --- GESTIÓN DE DEPENDENCIAS ---
def listar_dependencias(db: Session) -> List[Dict[str, Any]]:
    """Lista todas las dependencias"""
    try:
        resultados = db.execute(
            text("SELECT iddependencia, nomdependencia, siglas FROM usuarios.dependencias ORDER BY nomdependencia")
        ).mappings().all()
        
        return [dict(row) for row in resultados]
    except Exception as e:
        logger.error(f"Error listando dependencias: {e}")
        raise

def actualizar_empleado(
    db: Session, 
    email: str, 
    datos: Dict[str, Any],
    actualizado_por: str
) -> Dict[str, Any]:
    """Actualiza los datos de un empleado"""
    try:
        from sqlalchemy.dialects.postgresql import UUID as PGUUID
        from sqlalchemy import bindparam
        
        # Construir la consulta dinámicamente
        campos = []
        parametros = {"email": email, "actualizado_por": actualizado_por}
        
        # Mapeo de campos del schema a la base de datos
        mapeo_campos = {
            "nombre": "Nombre",
            "idDependencia": "IdDependencia",
            "dniJefeInmediato": "DniJefeInmediato"
        }
        
        for campo_schema, campo_db in mapeo_campos.items():
            if campo_schema in datos and datos[campo_schema] is not None:
                if campo_schema == "nombre":
                    campos.append(f"{campo_db} = :{campo_schema}")
                    parametros[campo_schema] = datos[campo_schema].upper()
                else:
                    campos.append(f"{campo_db} = :{campo_schema}")
                    parametros[campo_schema] = datos[campo_schema]
        
        if not campos:
            return {"mensaje": "No hay datos para actualizar", "email": email}
        
        campos.append("ActualizadoEn = CURRENT_DATE")
        campos.append("ActualizadoPor = :actualizado_por")
        
        consulta = f"""
            UPDATE usuarios.Empleados 
            SET {', '.join(campos)}
            WHERE LOWER(EmailInstitucional) = LOWER(:email)
        """
        
        if "idDependencia" in parametros:
            query = text(consulta).bindparams(
                bindparam("idDependencia", type_=PGUUID)
            )
        else:
            query = text(consulta)
        
        resultado = db.execute(query, parametros)
        
        if resultado.rowcount == 0:
            raise ValueError("Empleado no encontrado")
        
        db.commit()
        return {"mensaje": "Empleado actualizado exitosamente", "email": email}
    except ValueError:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error actualizando empleado: {e}")
        raise

def cambiar_estado_empleado(db: Session, email: str, activo: bool) -> Dict[str, Any]:
    """Activa o desactiva un empleado (da de baja)"""
    try:
        # Actualizar todos los roles del empleado
        resultado = db.execute(
            text("""
                UPDATE acceso.Empleados_Roles 
                SET ActLaboralmente = :activo,
                    ActualizadoEn = CURRENT_DATE
                WHERE LOWER(EmailInstitucional) = LOWER(:email)
            """),
            {"email": email, "activo": activo}
        )
        
        if resultado.rowcount == 0:
            raise ValueError("Empleado no encontrado")
        
        db.commit()
        estado = "activado" if activo else "dado de baja"
        return {
            "mensaje": f"Empleado {estado} exitosamente", 
            "email": email,
            "activo": activo
        }
    except ValueError:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error cambiando estado empleado: {e}")
        raise

def cambiar_contrasena_empleado(
    db: Session, 
    email: str, 
    nueva_contrasena: str
) -> Dict[str, Any]:
    """Cambia la contraseña de un empleado para todos sus roles"""
    try:
        resultado = db.execute(
            text("""
                UPDATE acceso.Empleados_Roles 
                SET Contrasena = :contrasena,
                    ActualizadoEn = CURRENT_DATE
                WHERE LOWER(EmailInstitucional) = LOWER(:email)
            """),
            {"email": email, "contrasena": nueva_contrasena}
        )
        
        if resultado.rowcount == 0:
            raise ValueError("Empleado no encontrado")
        
        db.commit()
        return {
            "mensaje": "Contraseña actualizada exitosamente", 
            "email": email,
            "rolesActualizados": resultado.rowcount
        }
    except ValueError:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error cambiando contraseña: {e}")
        raise

def eliminar_rol_empleado(
    db: Session, 
    email: str, 
    id_rol: str
) -> Dict[str, Any]:
    """Elimina un rol específico de un empleado"""
    try:
        from sqlalchemy.dialects.postgresql import UUID as PGUUID
        from sqlalchemy import bindparam
        
        query = text("""
            DELETE FROM acceso.Empleados_Roles
            WHERE LOWER(EmailInstitucional) = LOWER(:email) AND IdRol = :id_rol
        """).bindparams(
            bindparam("id_rol", type_=PGUUID)
        )
        
        resultado = db.execute(query, {"email": email, "id_rol": id_rol})
        
        if resultado.rowcount == 0:
            raise ValueError("Rol no encontrado para este empleado")
        
        db.commit()
        return {
            "mensaje": "Rol eliminado exitosamente", 
            "email": email
        }
    except ValueError:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error eliminando rol: {e}")
        raise

def crear_dependencia(
    db: Session, 
    datos: Dict[str, Any],
    creado_por: str
) -> Dict[str, Any]:
    """Crea una nueva dependencia"""
    try:
        from sqlalchemy.dialects.postgresql import UUID as PGUUID
        
        # Verificar si ya existe
        existe = db.execute(
            text("""
                SELECT 1 FROM usuarios.Dependencias 
                WHERE LOWER(NomDependencia) = LOWER(:nombre) 
                   OR LOWER(Siglas) = LOWER(:sigla)
            """),
            {"nombre": datos["nomdependencia"], "sigla": datos["sigla"]}
        ).first()
        
        if existe:
            raise ValueError("Ya existe una dependencia con ese nombre o sigla")
        
        nuevo_id = uuid4()
        db.execute(
            text("""
                INSERT INTO usuarios.Dependencias 
                (IdDependencia, NomDependencia, CodObjeto, Siglas, CreadoEn, CreadoPor) 
                VALUES (:id, :nombre, :cod_objeto, :siglas, CURRENT_DATE, :creado_por)
            """),
            {
                "id": nuevo_id, 
                "nombre": datos["nomdependencia"].upper(), 
                "cod_objeto": datos.get("idPrograma", 1),
                "siglas": datos["sigla"].upper(),
                "creado_por": creado_por
            }
        )
        db.commit()
        
        return {
            "mensaje": "Dependencia creada exitosamente", 
            "iddependencia": str(nuevo_id),
            "nombre": datos["nomdependencia"]
        }
    except ValueError:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creando dependencia: {e}")
        raise

def actualizar_dependencia(
    db: Session,
    id_dependencia: str,
    datos: Dict[str, Any],
    actualizado_por: str
) -> Dict[str, Any]:
    """Actualiza una dependencia existente"""
    try:
        from sqlalchemy.dialects.postgresql import UUID as PGUUID
        from sqlalchemy import bindparam
        
        campos = []
        parametros = {"id": id_dependencia, "actualizado_por": actualizado_por}
        
        if "nomdependencia" in datos and datos["nomdependencia"]:
            campos.append("NomDependencia = :nombre")
            parametros["nombre"] = datos["nomdependencia"].upper()
        
        if "sigla" in datos and datos["sigla"]:
            campos.append("Siglas = :sigla")
            parametros["sigla"] = datos["sigla"].upper()
        
        if not campos:
            return {"mensaje": "No hay datos para actualizar", "iddependencia": id_dependencia}
        
        campos.append("ActualizadoEn = CURRENT_DATE")
        campos.append("ActualizadoPor = :actualizado_por")
        
        consulta = f"""
            UPDATE usuarios.Dependencias 
            SET {', '.join(campos)}
            WHERE IdDependencia = :id
        """
        
        query = text(consulta).bindparams(
            bindparam("id", type_=PGUUID)
        )
        
        resultado = db.execute(query, parametros)
        
        if resultado.rowcount == 0:
            raise ValueError("Dependencia no encontrada")
        
        db.commit()
        return {
            "mensaje": "Dependencia actualizada exitosamente", 
            "iddependencia": id_dependencia
        }
    except ValueError:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error actualizando dependencia: {e}")
        raise

def eliminar_dependencia(db: Session, id_dependencia: str) -> Dict[str, Any]:
    """Elimina una dependencia si no tiene empleados asociados"""
    try:
        from sqlalchemy.dialects.postgresql import UUID as PGUUID
        from sqlalchemy import bindparam
        
        # Verificar si tiene empleados
        query_check = text("""
            SELECT COUNT(*) FROM usuarios.Empleados 
            WHERE IdDependencia = :id
        """).bindparams(
            bindparam("id", type_=PGUUID)
        )
        
        count = db.execute(query_check, {"id": id_dependencia}).scalar()
        
        if count > 0:
            raise ValueError(f"No se puede eliminar la dependencia porque tiene {count} empleado(s) asociado(s)")
        
        query_delete = text("""
            DELETE FROM usuarios.Dependencias 
            WHERE IdDependencia = :id
        """).bindparams(
            bindparam("id", type_=PGUUID)
        )
        
        resultado = db.execute(query_delete, {"id": id_dependencia})
        
        if resultado.rowcount == 0:
            raise ValueError("Dependencia no encontrada")
        
        db.commit()
        return {"mensaje": "Dependencia eliminada exitosamente"}
    except ValueError:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error eliminando dependencia: {e}")
        raise

def crear_rol(db: Session, datos: Dict[str, Any]) -> Dict[str, Any]:
    """Crea un nuevo rol"""
    try:
        # Verificar si ya existe
        existe = db.execute(
            text("""
                SELECT 1 FROM acceso.Roles 
                WHERE LOWER(NomRol) = LOWER(:nombre)
            """),
            {"nombre": datos["nomrol"]}
        ).first()
        
        if existe:
            raise ValueError("Ya existe un rol con ese nombre")
        
        query = text("""
            INSERT INTO acceso.Roles (NomRol, DesRol) 
            VALUES (:nombre, :descripcion)
            RETURNING IdRol
        """)
        
        resultado = db.execute(query, {
            "nombre": datos["nomrol"],
            "descripcion": datos.get("descripcion", "")
        }).fetchone()
        
        db.commit()
        
        return {
            "mensaje": "Rol creado exitosamente",
            "idrol": resultado[0],
            "nombre": datos["nomrol"]
        }
    except ValueError:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creando rol: {e}")
        raise

def actualizar_rol(
    db: Session,
    id_rol: int,
    datos: Dict[str, Any]
) -> Dict[str, Any]:
    """Actualiza un rol existente"""
    try:
        campos = []
        parametros = {"id": id_rol}
        
        if "nomrol" in datos and datos["nomrol"]:
            campos.append("NomRol = :nombre")
            parametros["nombre"] = datos["nomrol"]
        
        if "descripcion" in datos:
            campos.append("DesRol = :descripcion")
            parametros["descripcion"] = datos["descripcion"]
        
        if not campos:
            return {"mensaje": "No hay datos para actualizar", "idrol": id_rol}
        
        consulta = f"""
            UPDATE acceso.Roles 
            SET {', '.join(campos)}
            WHERE IdRol = :id
        """
        
        resultado = db.execute(text(consulta), parametros)
        
        if resultado.rowcount == 0:
            raise ValueError("Rol no encontrado")
        
        db.commit()
        return {
            "mensaje": "Rol actualizado exitosamente",
            "idrol": id_rol
        }
    except ValueError:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error actualizando rol: {e}")
        raise

def eliminar_rol(db: Session, id_rol: int) -> Dict[str, Any]:
    """Elimina un rol si no tiene empleados asociados"""
    try:
        # Verificar si tiene empleados
        count = db.execute(
            text("""
                SELECT COUNT(*) FROM acceso.Empleados_Roles 
                WHERE IdRol = :id
            """),
            {"id": id_rol}
        ).scalar()
        
        if count > 0:
            raise ValueError(f"No se puede eliminar el rol porque tiene {count} empleado(s) asignado(s)")
        
        resultado = db.execute(
            text("DELETE FROM acceso.Roles WHERE IdRol = :id"),
            {"id": id_rol}
        )
        
        if resultado.rowcount == 0:
            raise ValueError("Rol no encontrado")
        
        db.commit()
        return {"mensaje": "Rol eliminado exitosamente"}
    except ValueError:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error eliminando rol: {e}")
        raise

# --- GESTIÓN DE PERMISOS PERSONALIZADOS ---
def obtener_modulos_personalizados(db: Session, email: str) -> List[str]:
    """Obtiene los módulos asignados al rol del empleado"""
    try:
        # Obtener módulos basados en el rol del empleado
        resultados = db.execute(
            text("""
                SELECT DISTINCT rm.Modulo 
                FROM acceso.Roles_Modulos rm
                JOIN acceso.Empleados_Roles er ON er.IdRol = rm.IdRol
                WHERE LOWER(TRIM(er.EmailInstitucional)) = LOWER(TRIM(:email))
            """),
            {"email": email}
        ).fetchall()
        
        return [row[0] for row in resultados]
    except Exception as e:
        logger.warning(f"Error obteniendo módulos del empleado: {e}")
        return []

def asignar_modulos_personalizados(db: Session, admin_email: str, email: str, modulos: List[str]) -> Dict[str, Any]:
    """Asigna módulos al rol del empleado usando procedimientos almacenados"""
    try:
        # Obtener el rol del empleado
        empleado_rol = db.execute(
            text("""
                SELECT er.IdRol, r.NomRol 
                FROM acceso.Empleados_Roles er
                JOIN acceso.Roles r ON r.IdRol = er.IdRol
                WHERE LOWER(TRIM(er.EmailInstitucional)) = LOWER(TRIM(:email))
            """),
            {"email": email}
        ).first()
        
        if not empleado_rol:
            raise ValueError("Empleado no encontrado o sin rol asignado")
        
        # Limpiar módulos existentes del rol
        db.execute(
            text("DELETE FROM acceso.Roles_Modulos WHERE IdRol = :idrol"),
            {"idrol": empleado_rol[0]}
        )
        
        # Asignar nuevos módulos usando el procedimiento almacenado
        mensajes = []
        for modulo in modulos:
            try:
                resultado = db.execute(
                    text("CALL acceso.AsignarModuloARol(:admin_email, :idrol, :modulo, '')"),
                    {"admin_email": admin_email, "idrol": empleado_rol[0], "modulo": modulo}
                ).fetchone()
                mensajes.append(f"Módulo {modulo}: OK")
            except Exception as mod_error:
                logger.warning(f"Error asignando módulo {modulo}: {mod_error}")
                mensajes.append(f"Módulo {modulo}: Error - {str(mod_error)}")
        
        db.commit()
        
        return {
            "mensaje": f"Módulos asignados al rol {empleado_rol[1]} del empleado {email}",
            "email": email,
            "rol": empleado_rol[1],
            "total_modulos": len(modulos),
            "modulos": modulos,
            "detalles": mensajes
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error asignando módulos: {e}")
        raise

def obtener_empleados_con_permisos_completos(db: Session) -> List[Dict[str, Any]]:
    """Obtiene todos los empleados con información completa de permisos"""
    try:
        # Consulta principal de empleados
        empleados = db.execute(
            text("""
                SELECT 
                    e.emailinstitucional,
                    e.nombre as nombres,
                    '' as apellidos,
                    e.dni,
                    er.actlaboralmente,
                    er.ultimologin,
                    er.idrol,
                    r.nomrol,
                    e.iddependencia,
                    d.nomdependencia
                FROM usuarios.empleados e
                LEFT JOIN acceso.empleados_roles er ON er.emailinstitucional = e.emailinstitucional
                LEFT JOIN acceso.roles r ON r.idrol = er.idrol
                LEFT JOIN usuarios.dependencias d ON d.iddependencia = e.iddependencia
                ORDER BY e.nombre
            """)
        ).mappings().all()
        
        resultado = []
        for emp in empleados:
            empleado_dict = dict(emp)
            email = empleado_dict['emailinstitucional']
            
            # Obtener módulos del rol si existen
            try:
                modulos_rol = db.execute(
                    text("""
                        SELECT DISTINCT rm.Modulo 
                        FROM acceso.Roles_Modulos rm
                        WHERE rm.IdRol = :idrol
                    """),
                    {"idrol": empleado_dict['idrol']}
                ).fetchall() if empleado_dict['idrol'] else []
                
                empleado_dict['modulos_asignados'] = [row[0] for row in modulos_rol]
                empleado_dict['tiene_modulos_asignados'] = len(modulos_rol) > 0
            except Exception:
                empleado_dict['modulos_asignados'] = []
                empleado_dict['tiene_modulos_asignados'] = False

            # Obtener módulos personalizados (actualmente no implementado)
            empleado_dict['modulos_personalizados'] = []
            empleado_dict['tiene_permisos_personalizados'] = False
            
            resultado.append(empleado_dict)
        
        return resultado
    except Exception as e:
        logger.error(f"Error obteniendo empleados con permisos: {e}")
        raise

def eliminar_permisos_personalizados(db: Session, email: str) -> Dict[str, Any]:
    """Elimina módulos asignados al rol del empleado"""
    try:
        # Obtener el rol del empleado
        empleado_rol = db.execute(
            text("""
                SELECT IdRol 
                FROM acceso.Empleados_Roles
                WHERE LOWER(TRIM(EmailInstitucional)) = LOWER(TRIM(:email))
            """),
            {"email": email}
        ).first()
        
        if not empleado_rol:
            raise ValueError("Empleado no encontrado")
        
        # Eliminar módulos del rol
        resultado = db.execute(
            text("DELETE FROM acceso.Roles_Modulos WHERE IdRol = :idrol"),
            {"idrol": empleado_rol[0]}
        )
        
        db.commit()
        
        return {
            "mensaje": f"Módulos del rol eliminados para {email}.",
            "email": email
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error eliminando permisos personalizados: {e}")
        raise

# --- ESTADÍSTICAS ---
def obtener_estadisticas_admin(db: Session) -> Dict[str, Any]:
    """Obtiene estadísticas generales del sistema para el administrador"""
    try:
        # Estadísticas de empleados
        empleados = db.execute(
            text("""
                SELECT 
                    COUNT(e.*) as total,
                    COUNT(CASE WHEN er.actlaboralmente = true THEN 1 END) as activos
                FROM usuarios.empleados e
                LEFT JOIN acceso.empleados_roles er ON er.emailinstitucional = e.emailinstitucional
            """)
        ).mappings().first()
        
        # Estadísticas de roles y dependencias
        roles = db.execute(text("SELECT COUNT(*) as total FROM acceso.roles")).scalar()
        dependencias = db.execute(text("SELECT COUNT(*) as total FROM usuarios.dependencias")).scalar()
        
        # Estadísticas de requisiciones (tabla correcta)
        try:
            requisiciones = db.execute(
                text("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(CASE WHEN estgeneral = 'EN ESPERA' THEN 1 END) as pendientes,
                        COUNT(CASE WHEN estgeneral = 'APROBADO' THEN 1 END) as aprobadas
                    FROM requisiciones.requisiciones
                """)
            ).mappings().first()
        except Exception as e:
            logger.warning(f"Error obteniendo estadísticas de requisiciones: {e}")
            requisiciones = {"total": 0, "pendientes": 0, "aprobadas": 0}
        
        # Estadísticas de productos (sin columna activo)
        try:
            productos = db.execute(
                text("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(CASE WHEN canstock > 0 THEN 1 END) as activos
                    FROM productos.productos
                """)
            ).mappings().first()
        except Exception as e:
            logger.warning(f"Error obteniendo estadísticas de productos: {e}")
            productos = {"total": 0, "activos": 0}
        
        return {
            "total_empleados": empleados["total"],
            "empleados_activos": empleados["activos"],
            "total_roles": roles,
            "total_dependencias": dependencias,
            "total_requisiciones": requisiciones["total"],
            "requisiciones_pendientes": requisiciones["pendientes"],
            "requisiciones_aprobadas": requisiciones["aprobadas"],
            "total_productos": productos["total"],
            "productos_activos": productos["activos"]
        }
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        raise

# ==================== FUNCIONES PARA INTERFAZ ADMIN ====================

def obtener_todas_dependencias(db: Session) -> List[Dict[str, Any]]:
    """Obtiene todas las dependencias ordenadas por nombre"""
    query = text("""
        SELECT 
            IdDependencia as iddependencia,
            NomDependencia as nomdependencia,
            CodPrograma as idprograma,
            Siglas as sigla,
            CreadoEn as creadoen
        FROM usuarios.Dependencias
        ORDER BY NomDependencia
    """)
    
    result = db.execute(query).mappings().all()
    return [dict(row) for row in result]

def obtener_todos_roles(db: Session) -> List[Dict[str, Any]]:
    """Obtiene todos los roles disponibles"""
    query = text("""
        SELECT 
            IdRol as idrol,
            NomRol as nomrol,
            NULL::text as desrol
        FROM acceso.Roles
        ORDER BY NomRol
    """)
    
    result = db.execute(query).mappings().all()
    return [dict(row) for row in result]

def obtener_todos_empleados(db: Session) -> List[Dict[str, Any]]:
    """Obtiene todos los empleados con su dependencia y roles"""
    query = text("""
        SELECT 
            e.EmailInstitucional as emailinstitucional,
            e.Nombre as nombre,
            e.Dni as dni,
            e.DniJefeInmediato as dnijefeinmediato,
            d.NomDependencia as nomdependencia,
            d.Siglas as sigladependencia,
            e.IdDependencia as iddependencia,
            jefe.Nombre as nombrejefeinmediato,
            string_agg(DISTINCT r.NomRol, ', ' ORDER BY r.NomRol) as roles,
            COALESCE(BOOL_OR(er.ActLaboralmente), FALSE) as activo,
            e.CreadoEn as creadoen
        FROM usuarios.Empleados e
        INNER JOIN usuarios.Dependencias d ON e.IdDependencia = d.IdDependencia
        LEFT JOIN usuarios.Empleados jefe ON e.DniJefeInmediato = jefe.Dni
        LEFT JOIN acceso.Empleados_Roles er ON LOWER(e.EmailInstitucional) = LOWER(er.EmailInstitucional)
        LEFT JOIN acceso.Roles r ON er.IdRol = r.IdRol
        GROUP BY 
            e.EmailInstitucional, e.Nombre, e.Dni, e.DniJefeInmediato,
            d.NomDependencia, d.Siglas, e.IdDependencia, jefe.Nombre, e.CreadoEn
        ORDER BY e.Nombre
    """)
    
    result = db.execute(query).mappings().all()
    return [dict(row) for row in result]

def buscar_empleado_por_dni(db: Session, dni: str) -> Dict[str, Any] | None:
    """Busca un empleado por DNI para validaciones"""
    query = text("""
        SELECT 
            EmailInstitucional,
            Nombre,
            Dni,
            IdDependencia
        FROM usuarios.Empleados
        WHERE Dni = :dni
        LIMIT 1
    """)
    
    result = db.execute(query, {"dni": dni}).mappings().first()
    return dict(result) if result else None

def crear_empleado_completo(
    db: Session,
    email: str,
    nombre: str,
    id_dependencia: UUID,
    dni: str,
    dni_jefe: str | None,
    creado_por: str
) -> Dict[str, Any]:
    """Crea un nuevo empleado"""
    from sqlalchemy.dialects.postgresql import UUID as PGUUID
    from sqlalchemy import bindparam
    
    query = text("""
        INSERT INTO usuarios.Empleados
        (EmailInstitucional, Nombre, IdDependencia, Dni, DniJefeInmediato, CreadoEn, CreadoPor)
        VALUES
        (:email, :nombre, :id_dependencia, :dni, :dni_jefe, CURRENT_DATE, :creado_por)
        RETURNING EmailInstitucional, Nombre, Dni
    """).bindparams(
        bindparam("id_dependencia", type_=PGUUID)
    )
    
    params = {
        "email": email,
        "nombre": nombre,
        "id_dependencia": id_dependencia,
        "dni": dni,
        "dni_jefe": dni_jefe,
        "creado_por": creado_por
    }
    
    result = db.execute(query, params).mappings().first()
    db.commit()
    return dict(result)

def asignar_rol_empleado_con_password(
    db: Session,
    email: str,
    id_rol: UUID,
    contrasena: str,
    creado_por: str
) -> None:
    """Asigna un rol y contraseña a un empleado (versión extendida para crear usuarios)"""
    from sqlalchemy.dialects.postgresql import UUID as PGUUID
    from sqlalchemy import bindparam
    
    # Verificar si ya existe este empleado-rol
    check_query = text("""
        SELECT 1 FROM acceso.Empleados_Roles
        WHERE LOWER(EmailInstitucional) = LOWER(:email) AND IdRol = :id_rol
    """).bindparams(
        bindparam("id_rol", type_=PGUUID)
    )
    
    existe = db.execute(check_query, {"email": email, "id_rol": id_rol}).first()
    
    if existe:
        # Actualizar registro existente
        update_query = text("""
            UPDATE acceso.Empleados_Roles
            SET Contrasena = :contrasena,
                ActLaboralmente = TRUE,
                ActualizadoEn = CURRENT_DATE,
                ActualizadoPor = :creado_por
            WHERE LOWER(EmailInstitucional) = LOWER(:email) AND IdRol = :id_rol
        """).bindparams(
            bindparam("id_rol", type_=PGUUID)
        )
        db.execute(update_query, {
            "email": email,
            "id_rol": id_rol,
            "contrasena": contrasena,
            "creado_por": creado_por
        })
    else:
        # Insertar nuevo registro
        insert_query = text("""
            INSERT INTO acceso.Empleados_Roles
            (EmailInstitucional, IdRol, Contrasena, ActLaboralmente, CreadoEn, CreadoPor)
            VALUES
            (:email, :id_rol, :contrasena, TRUE, CURRENT_DATE, :creado_por)
        """).bindparams(
            bindparam("id_rol", type_=PGUUID)
        )
        db.execute(insert_query, {
            "email": email,
            "id_rol": id_rol,
            "contrasena": contrasena,
            "creado_por": creado_por
        })
    
    db.commit()