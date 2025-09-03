from sqlalchemy import String, Date, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from datetime import date
from app.core.database import Base

class Aprobacion(Base):
    __tablename__ = "Aprobaciones"
    __table_args__ = {"schema": "requisiciones"}

    IdAprobacion: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    IdRequisicion: Mapped[str | None] = mapped_column(UUID(as_uuid=True))
    EmailInstitucional: Mapped[str | None] = mapped_column(String(50))
    Rol: Mapped[str | None] = mapped_column(String(50))
    EstadoAprobacion: Mapped[str | None] = mapped_column(String(20))
    Comentario: Mapped[str | None] = mapped_column(Text)
    FecAprobacion: Mapped[date | None] = mapped_column(Date)