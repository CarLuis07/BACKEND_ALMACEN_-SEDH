from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import settings
import traceback

class Base(DeclarativeBase):
    pass

engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,  # ajusta a tu variable actual
    echo=False,                        # asegura que NO haya echo
    pool_pre_ping=True,
    future=True,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
        # Si llegamos aquí sin excepciones, la transacción ya debería estar commiteada
        # No hacemos rollback automático
    except Exception:
        # Solo hacer rollback si hubo error
        db.rollback()
        raise
    finally:
        db.close()

def test_db_connection():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, "OK"
    except Exception as e:
        detail = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
        return False, detail
