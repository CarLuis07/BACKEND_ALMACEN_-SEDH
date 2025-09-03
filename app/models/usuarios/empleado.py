from sqlalchemy import String, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from datetime import date
from app.core.database import Base

class Empleado(Base):
    __tablename__ = "Empleados"
    __table_args__ = {"schema": "usuarios"}

    EmailInstitucional: Mapped[str] = mapped_column(String(50), primary_key=True)
    Nombre: Mapped[str | None] = mapped_column(String(100))
    IdDependencia: Mapped[str | None] = mapped_column(UUID(as_uuid=True))
    DNI: Mapped[str | None] = mapped_column(String(13))
    DNIJefeInmediato: Mapped[str | None] = mapped_column(String(13))
    CreadoEn: Mapped[date | None] = mapped_column(Date)
    CreadoPor: Mapped[str | None] = mapped_column(String(50))
    ActualizadoEn: Mapped[date | None] = mapped_column(Date)
    ActualizadoPor: Mapped[str | None] = mapped_column(String(50))