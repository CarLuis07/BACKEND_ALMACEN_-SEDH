from sqlalchemy import String, Date, Numeric, Integer, Text, func, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from datetime import date, datetime
from decimal import Decimal
from app.core.database import Base

class Requisicion(Base):
    __tablename__ = "Requisiciones"
    __table_args__ = {"schema": "requisiciones"}

    IdRequisicion: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    CodRequisicion: Mapped[str | None] = mapped_column(String(50))
    NomEmpleado: Mapped[str | None] = mapped_column(String(100))
    IdDependencia: Mapped[str | None] = mapped_column(UUID(as_uuid=True))
    FecSolicitud: Mapped[date | None] = mapped_column(Date)
    CodPrograma: Mapped[str | None] = mapped_column(UUID(as_uuid=True))
    ProIntermedio: Mapped[Decimal | None] = mapped_column(Numeric(10,2))
    ProFinal: Mapped[int | None] = mapped_column(Integer)
    EstGeneral: Mapped[str | None] = mapped_column(String(50))
    ObsEmpleado: Mapped[str | None] = mapped_column(Text)
    ObsAlmacen: Mapped[str | None] = mapped_column(Text)
    MotRechazo: Mapped[str | None] = mapped_column(Text)
    GasTotalDelPedido: Mapped[Decimal | None] = mapped_column(Numeric(14,2))
    ReqEntregadoPor: Mapped[str | None] = mapped_column(String(50))
    ReqRecibidoPor: Mapped[str | None] = mapped_column(String(50))
    CreadoEn: Mapped[date | None] = mapped_column(Date)
    CreadoPor: Mapped[str | None] = mapped_column(String(50))
    ActualizadoEn: Mapped[date | None] = mapped_column(Date)
    ActualizadoPor: Mapped[str | None] = mapped_column(String(50))
    # Nuevos campos de timestamp para auditoría
    FechaHoraCreacion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    FechaHoraEnvio: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    FechaHoraAprobacionJefe: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    FechaHoraAprobacionAlmacen: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    FechaHoraRechazo: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    FechaHoraEntrega: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    IdEmpleadoCreador: Mapped[str | None] = mapped_column(UUID(as_uuid=True))
    IdJefeAprobador: Mapped[str | None] = mapped_column(UUID(as_uuid=True))
    IdAlmacenAprobador: Mapped[str | None] = mapped_column(UUID(as_uuid=True))