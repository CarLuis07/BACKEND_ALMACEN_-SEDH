from sqlalchemy import String, Date, Numeric, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from datetime import date
from app.core.database import Base
from decimal import Decimal

class Producto(Base):
    __tablename__ = "Productos"
    __table_args__ = {"schema": "productos"}

    IdProducto: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    CodObjetoUnico: Mapped[str | None] = mapped_column(Text)
    IdCategoria: Mapped[str | None] = mapped_column(UUID(as_uuid=True))
    FecIngreso: Mapped[date | None] = mapped_column(Date)
    NomProducto: Mapped[str | None] = mapped_column(String(100))
    DescProducto: Mapped[str | None] = mapped_column(Text)
    CanStockInicial: Mapped[Decimal | None] = mapped_column(Numeric(10,2)) 
    CanStock: Mapped[Decimal | None] = mapped_column(Numeric(10,2))
    Proveedor: Mapped[str | None] = mapped_column(String(100))
    LimStockBajo: Mapped[Decimal | None] = mapped_column(Numeric(10,2))
    LimAproGerente: Mapped[Decimal | None] = mapped_column(Numeric(10,2))
    FecVencimiento: Mapped[date | None] = mapped_column(Date)
    IdUnidadMedida: Mapped[str | None] = mapped_column(UUID(as_uuid=True))
    GasUnitario: Mapped[Decimal | None] = mapped_column(Numeric(12,2))
    GasTotalInicial: Mapped[Decimal | None] = mapped_column(Numeric(12,2))
    GasTotal: Mapped[Decimal | None] = mapped_column(Numeric(14,2))
    CreadoEn: Mapped[date | None] = mapped_column(Date)
    CreadoPor: Mapped[str | None] = mapped_column(String(50))
    ActualizadoEn: Mapped[date | None] = mapped_column(Date)
    ActualizadoPor: Mapped[str | None] = mapped_column(String(50))