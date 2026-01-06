from sqlalchemy import String, DateTime, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.core.database import Base


class AuditoriaRequisicion(Base):
    __tablename__ = "auditoria_requisiciones"
    __table_args__ = {"schema": "requisiciones"}

    IdAuditoria: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    IdRequisicion: Mapped[str | None] = mapped_column(UUID(as_uuid=True))
    TipoAccion: Mapped[str | None] = mapped_column(String(50))  # CREADA, ENVIADA, APROBADA_JEFE, APROBADA_ALMACEN, RECHAZADA, ENTREGADA
    IdUsuarioAccion: Mapped[str | None] = mapped_column(UUID(as_uuid=True))
    NombreUsuarioAccion: Mapped[str | None] = mapped_column(String(100))
    DescripcionAccion: Mapped[str | None] = mapped_column(Text)
    FechaHoraAccion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    Observaciones: Mapped[str | None] = mapped_column(Text)
    CreatedAt: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
