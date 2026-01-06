from sqlalchemy import String, Date, Boolean, ForeignKey, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from datetime import date, datetime
from app.core.database import Base

class EmpleadoRol(Base):
    __tablename__ = "Empleados_Roles"
    __table_args__ = {"schema": "acceso"}

    IdEmpleadoRol: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    EmailInstitucional: Mapped[str | None] = mapped_column(String(50), index=True)
    IdRol: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("acceso.Roles.IdRol"))
    Contrasena: Mapped[str | None] = mapped_column(String(100))
    ActLaboralmente: Mapped[bool | None] = mapped_column(Boolean)
    UltimoLogin: Mapped[datetime | None] = mapped_column(TIMESTAMP)
    CreadoEn: Mapped[date | None] = mapped_column(Date)
    CreadoPor: Mapped[str | None] = mapped_column(String(50))
    ActualizadoEn: Mapped[date | None] = mapped_column(Date)
    ActualizadoPor: Mapped[str | None] = mapped_column(String(50))