from pydantic import BaseModel
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    PROJECT_NAME: str = "Backend Almacén SEDH"
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8
    DB_HOST: str
    DB_PORT: int = 5432
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    ENV: str = "dev"
    
    # Configuración SMTP
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        # Usando psycopg2 (más estable y compatible)
        return (f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}"
                f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}")

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"  # Permitir variables extra en .env
        extra = "allow"  # Permitir variables extra en .env

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
