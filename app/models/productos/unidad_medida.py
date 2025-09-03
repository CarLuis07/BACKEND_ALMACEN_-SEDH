from sqlalchemy import String, Date, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from datetime import date
from app.core.database import Base

class UnidadMedida(Base):
    __tablename__ = "Unidades_Medida"
    __table_args__ = {"schema": "productos"}

    IdUnidadMedida: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    NomUnidad: Mapped[str | None] = mapped_column(String(50))
    CreadoEn: Mapped[date | None] = mapped_column(Date)
    CreadoPor: Mapped[str | None] = mapped_column(String(50))