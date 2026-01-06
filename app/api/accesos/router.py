import sys
import os
# Configurar PYTHONPATH automáticamente
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.repositories.accesos import login_empleado, obtener_info_empleado
from app.core.security import create_access_token, get_current_user
from app.schemas.accesos.login import LoginRequest, TokenResponse

router = APIRouter()

@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    ok, rol = login_empleado(db, data.email, data.password)
    if not ok:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")

    # Incluimos el rol en los claims del token; expira en 4 horas (por defecto en create_access_token)
    token = create_access_token(subject=data.email, extra_claims={"rol": rol})
    return TokenResponse(access_token=token)

@router.get("/me",
        summary="obtener información del usuario actual")
def me(claims = Depends(get_current_user), db: Session = Depends(get_db)):
    email = claims.get("sub")
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    
    info_empleado = obtener_info_empleado(db, email)
    if not info_empleado:
        # Fallback a información básica del token
        return {"email": email, "rol": claims.get("rol"), "exp": claims.get("exp")}
    
    return {
        **info_empleado,
        "exp": claims.get("exp")
    }

@router.get("/modulos", summary="Obtener módulos del usuario actual")
def obtener_modulos_usuario(claims = Depends(get_current_user), db: Session = Depends(get_db)):
    """Obtiene los módulos específicos del usuario actual"""
    email = claims.get("sub")
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    
    try:
        from sqlalchemy import text
        
        modulos_totales = set()
        tipos_fuente = []
        
        # Verificar módulos personalizados
        query_personalizados = text("""
            SELECT modulo 
            FROM acceso.empleados_modulos_personalizados 
            WHERE LOWER(TRIM(emailinstitucional)) = LOWER(TRIM(:email)) 
            AND activo = true
        """)
        
        modulos_personalizados = db.execute(query_personalizados, {"email": email}).fetchall()
        
        if modulos_personalizados:
            modulos_pers = [row[0] for row in modulos_personalizados]
            modulos_totales.update(modulos_pers)
            tipos_fuente.append("PERSONALIZADOS")
        
        # Módulos del rol
        query_rol = text("""
            SELECT DISTINCT rm.Modulo 
            FROM acceso.Roles_Modulos rm
            JOIN acceso.Empleados_Roles er ON er.IdRol = rm.IdRol
            WHERE LOWER(TRIM(er.EmailInstitucional)) = LOWER(TRIM(:email))
        """)
        
        modulos_rol = db.execute(query_rol, {"email": email}).fetchall()
        
        if modulos_rol:
            modulos_rol_list = [row[0] for row in modulos_rol]
            modulos_totales.update(modulos_rol_list)
            tipos_fuente.append("POR_ROL")
        
        # Devolver todos los módulos combinados
        modulos_finales = list(modulos_totales)
        tipo_final = " + ".join(tipos_fuente) if tipos_fuente else "SIN_PERMISOS"
        
        return {"modulos": modulos_finales, "tipo": tipo_final}
            
    except Exception as e:
        # En caso de error, dar permisos básicos según rol
        rol = claims.get("rol", "")
        if rol == "Administrador":
            modulos = ["dashboard", "productos", "categorias", "agregar_producto", "requisiciones", "mis_requisiciones", "movimientos", "accesos", "administracion"]
        else:
            modulos = ["dashboard"]
        
        return {"modulos": modulos, "tipo": "ERROR_FALLBACK", "error": str(e)}

@router.get("/mis-modulos", summary="Obtener módulos disponibles para el usuario actual")
def obtener_mis_modulos(claims = Depends(get_current_user), db: Session = Depends(get_db)):
    """Obtiene los módulos específicos del usuario actual basado en sus permisos personalizados o rol"""
    email = claims.get("sub")
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    
    try:
        from sqlalchemy import text
        
        # Primero verificar si tiene módulos personalizados
        modulos_personalizados = db.execute(
            text("""
                SELECT modulo 
                FROM acceso.empleados_modulos_personalizados 
                WHERE LOWER(TRIM(emailinstitucional)) = LOWER(TRIM(:email)) 
                AND activo = true
            """),
            {"email": email}
        ).fetchall()
        
        if modulos_personalizados:
            # Si tiene módulos personalizados, usar solo esos
            modulos = [row[0] for row in modulos_personalizados]
            return {
                "modulos": modulos,
                "tipo_permisos": "PERSONALIZADOS",
                "total_modulos": len(modulos)
            }
        else:
            # Si no tiene módulos personalizados, usar los del rol
            modulos_rol = db.execute(
                text("""
                    SELECT DISTINCT rm.Modulo 
                    FROM acceso.Roles_Modulos rm
                    JOIN acceso.Empleados_Roles er ON er.IdRol = rm.IdRol
                    WHERE LOWER(TRIM(er.EmailInstitucional)) = LOWER(TRIM(:email))
                """),
                {"email": email}
            ).fetchall()
            
            modulos = [row[0] for row in modulos_rol]
            return {
                "modulos": modulos,
                "tipo_permisos": "POR_ROL",
                "total_modulos": len(modulos)
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo módulos: {str(e)}")
