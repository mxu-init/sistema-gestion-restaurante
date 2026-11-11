from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "SGR - Sistema Gestión Restaurante"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "ERP Restaurante Backend"

    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "sgr_db"
    DB_USER: str = "sgr_user"
    DB_PASSWORD: str = "postgres"
    DRIVER_NAME: str = "postgresql+psycopg"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def database_url(self) -> str:
        return (
            f"{self.DRIVER_NAME}://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )
    # database_url = postgresql+psycopg2://usuario:password@localhost:5432/test_db


settings = Settings()
