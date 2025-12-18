from pydantic import SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    API_KEY: SecretStr


config = Settings(_env_file=".env")
