from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.repositories.accesos import login_empleado
from app.core.security import create_access_token, get_current_user
from app.schemas.accesos.login import LoginRequest, TokenResponse

router = APIRouter()

@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    ok, rol = login_empleado(db, data.email, data.password)
    if not ok:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")

    # Incluimos el rol en los claims del token; expira en 4 horas (por defecto en create_access_token)
    token = create_access_token(subject=data.email, extra_claims={"role": rol})
    return TokenResponse(access_token=token)

@router.get("/me",
        summary="prueba token")
def me(claims = Depends(get_current_user)):
    return {"email": claims.get("sub"), "role": claims.get("role"), "exp": claims.get("exp")}