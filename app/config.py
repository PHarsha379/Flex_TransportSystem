from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./student_transport_dev.db"
    random_seed: int = 20261022
    data_year: int = 2026

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
