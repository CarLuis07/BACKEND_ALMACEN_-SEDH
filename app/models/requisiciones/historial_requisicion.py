from sqlalchemy import Date, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from datetime import date
from app.core.database import Base

class HistorialRequisicion(Base):
    __tablename__ = "Historial_Requisiciones"
    __table_args__ = {"schema": "requisiciones"}

    IdHistorialRequisicion: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    IdRequisicion: Mapped[str | None] = mapped_column(UUID(as_uuid=True))
    CreadoEn: Mapped[date | None] = mapped_column(Date)
    CreadoPor: Mapped[str | None] = mapped_column(String(50))