from sqlalchemy import String, Date, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from datetime import date
from app.core.database import Base

class Dependencia(Base):
    __tablename__ = "Dependencias"
    __table_args__ = {"schema": "usuarios"}

    IdDependencia: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    NomDependencia: Mapped[str | None] = mapped_column(String(100))
    CodPrograma: Mapped[str | None] = mapped_column(String(4))
    Siglas: Mapped[str | None] = mapped_column(String(5))
    CreadoEn: Mapped[date | None] = mapped_column(Date)
    CreadoPor: Mapped[str | None] = mapped_column(String(50))