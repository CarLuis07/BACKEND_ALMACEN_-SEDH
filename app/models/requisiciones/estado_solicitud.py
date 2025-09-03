from sqlalchemy import String, Date, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from datetime import date
from app.core.database import Base

class EstadoSolicitud(Base):
    __tablename__ = "Estado_Solicitudes"
    __table_args__ = {"schema": "requisiciones"}

    IdEstadoSolicitud: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    NomEstado: Mapped[str | None] = mapped_column(String(50))
    CreadoEn: Mapped[date | None] = mapped_column(Date)
    CreadoPor: Mapped[str | None] = mapped_column(String(50))