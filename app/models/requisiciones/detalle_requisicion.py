from sqlalchemy import String, Numeric, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from decimal import Decimal
from app.core.database import Base

class DetalleRequisicion(Base):
    __tablename__ = "Detalle_Requisicion"
    __table_args__ = {"schema": "requisiciones"}

    IdDetalleRequisicion: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    IdRequisicion: Mapped[str | None] = mapped_column(UUID(as_uuid=True))
    IdProducto: Mapped[str | None] = mapped_column(UUID(as_uuid=True))
    CantSolicitada: Mapped[Decimal | None] = mapped_column(Numeric(10,2))
    CantEntregada: Mapped[Decimal | None] = mapped_column(Numeric(10,2))
    GasUnitario: Mapped[Decimal | None] = mapped_column(Numeric(12,2))
    GasTotalProducto: Mapped[Decimal | None] = mapped_column(Numeric(14,2))
    EntregadoPor: Mapped[str | None] = mapped_column(String(100))
    RecibidoPor: Mapped[str | None] = mapped_column(String(100))