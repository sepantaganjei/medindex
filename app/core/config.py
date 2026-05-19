import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    app_host: str = os.getenv("APP_HOST", "0.0.0.0")
    app_port: int = int(os.getenv("APP_PORT", "8000"))
    app_reload: bool = os.getenv("APP_RELOAD", "false").lower() == "true"

    db_user: str = os.getenv("DB_USER", "postgres")
    db_password: str = os.getenv("DB_PASSWORD", "postgres")
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: str = os.getenv("DB_PORT", "5432")
    db_name: str = os.getenv("DB_NAME", "bioimages")
    object_storage_endpoint: str = os.getenv("OBJECT_STORAGE_ENDPOINT", "localhost:9000")
    object_storage_access_key: str = os.getenv("OBJECT_STORAGE_ACCESS_KEY", "minioadmin")
    object_storage_secret_key: str = os.getenv("OBJECT_STORAGE_SECRET_KEY", "minioadmin")
    object_storage_bucket: str = os.getenv("OBJECT_STORAGE_BUCKET", "bioimages")
    object_storage_secure: bool = os.getenv("OBJECT_STORAGE_SECURE", "false").lower() == "true"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


config = Config()
