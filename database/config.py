from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()
# redis Settings
redis_host = os.environ.get("REDIS_HOST")
redis_port = os.environ.get("REDIS_PORT")


# Load environment variables from "stack.env"
load_dotenv("stack.env")

# Define settings using Pydantic's BaseSettings
class Settings(BaseSettings):
    DB_HOST_SQL: str
    DB_PORT_SQL: int
    DB_USER_SQL: str
    DB_PASS_SQL: str
    DB_NAME: str

    @property
    def DATABASE_URL_asyncpg(self):
        return f"postgresql+asyncpg://{self.DB_USER_SQL}:{self.DB_PASS_SQL}@{self.DB_HOST_SQL}:{self.DB_PORT_SQL}/{self.DB_NAME}"

settings = Settings()

"""
# Instantiate the settings
settings = Settings()

# postgres Settings
class Settings(BaseSettings):
    DB_HOST_SQL: str
    DB_PORT_SQL: int
    DB_USER_SQL: str
    DB_PASS_SQL: str
    DB_NAME: str
    model_config = SettingsConfigDict(env_file="stack.env", extra="ignore")

    @property
    def DATABASE_URL_asyncpg(self):
        return f"postgresql+asyncpg://{self.DB_USER_SQL}:{self.DB_PASS_SQL}@{self.DB_HOST_SQL}:{self.DB_PORT_SQL}/{self.DB_NAME}"
    

"""