from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    kg_store_url: str = "http://localhost:8080"
    ts_db_url: str = ""   # empty → NullTsReader
    log_level: str = "INFO"


settings = Settings()
