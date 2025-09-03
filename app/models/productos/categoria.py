from sqlalchemy import String, Date, Numeric, LargeBinary, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from datetime import date
from app.core.database import Base

class Categoria(Base):
    __tablename__ = "Categorias"
    __table_args__ = {"schema": "productos"}

    IdCategoria: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    CodObjeto: Mapped[int | None] = mapped_column()
    NomCategoria: Mapped[str | None] = mapped_column(String(100))
    DesCategoria: Mapped[str | None] = mapped_column(String(100))
    Imagen: Mapped[bytes | None] = mapped_column(LargeBinary)
    CreadoEn: Mapped[date | None] = mapped_column(Date)
    CreadoPor: Mapped[str | None] = mapped_column(String(50))
    ActualizadoEn: Mapped[date | None] = mapped_column(Date)
    ActualizadoPor: Mapped[str | None] = mapped_column(String(50))