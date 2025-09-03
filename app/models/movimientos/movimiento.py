from sqlalchemy import String, Date, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from datetime import date, datetime
from app.core.database import Base

class Movimiento(Base):
    __tablename__ = "Movimientos"
    __table_args__ = {"schema": "movimientos"}

    IdMovimiento: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    FecMovimiento: Mapped[datetime | None] = mapped_column(TIMESTAMP)
    IdCategoria: Mapped[str | None] = mapped_column(UUID(as_uuid=True))
    IdProducto: Mapped[str | None] = mapped_column(UUID(as_uuid=True))
    IdRequisicion: Mapped[str | None] = mapped_column(UUID(as_uuid=True))
    IdTipoMovimiento: Mapped[str | None] = mapped_column(UUID(as_uuid=True))
    CreadoEn: Mapped[date | None] = mapped_column(Date)
    CreadoPor: Mapped[str | None] = mapped_column(String(50))
    ActualizadoEn: Mapped[date | None] = mapped_column(Date)
    ActualizadoPor: Mapped[str | None] = mapped_column(String(50))