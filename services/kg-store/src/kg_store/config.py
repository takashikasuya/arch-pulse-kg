from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    sparql_endpoint: str = "http://localhost:7878"
    nats_url: str = "nats://localhost:4222"
    nats_stream: str = "bldg"
    log_level: str = "INFO"
    tunnel_jwt_secret: str = "test-secret-replace-in-prod-min32b"


settings = Settings()
