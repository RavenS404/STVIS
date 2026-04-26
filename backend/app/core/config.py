from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Intelligent Traffic Violation Monitoring for Reliable and Affordable Road Safety"
    api_v1_prefix: str = "/api/v1"
    debug: bool = False
    secret_key: str = Field(default="change-me-in-production", alias="SECRET_KEY")
    access_token_expire_minutes: int = 60
    timezone: str = "Africa/Cairo"

    database_url: str = Field(
        default="postgresql+psycopg://stvis:stvis@postgres:5432/stvis",
        alias="DATABASE_URL",
    )

    rabbitmq_url: str = Field(
        default="amqp://stvis:stvis@rabbitmq:5672//",
        alias="RABBITMQ_URL",
    )
    rabbitmq_management_url: str = Field(
        default="http://rabbitmq:15672/api",
        alias="RABBITMQ_MANAGEMENT_URL",
    )
    rabbitmq_management_username: str = Field(default="stvis", alias="RABBITMQ_DEFAULT_USER")
    rabbitmq_management_password: str = Field(default="stvis", alias="RABBITMQ_DEFAULT_PASS")

    minio_endpoint: str = Field(default="minio:9000", alias="MINIO_ENDPOINT")
    minio_access_key: str = Field(default="minioadmin", alias="MINIO_ROOT_USER")
    minio_secret_key: str = Field(default="minioadmin", alias="MINIO_ROOT_PASSWORD")
    minio_secure: bool = Field(default=False, alias="MINIO_SECURE")
    minio_bucket: str = Field(default="stvis-evidence", alias="MINIO_BUCKET")

    frontend_origin: str = Field(default="http://localhost:8080", alias="FRONTEND_ORIGIN")
    cors_origins: str = Field(default="http://localhost:8080,http://frontend:80", alias="CORS_ORIGINS")

    max_upload_size_mb: int = 12
    allowed_image_mime_types: str = "image/jpeg,image/png,image/webp"

    violation_model_path: str = Field(
        default=str(Path("Ai_models") / "violation_detection.pt"),
        alias="VIOLATION_MODEL_PATH",
    )
    plate_model_path: str = Field(
        default=str(Path("Ai_models") / "plate_detection.pt"),
        alias="PLATE_MODEL_PATH",
    )

    default_admin_username: str = "admin"
    default_admin_password: str = "Admin@123456"
    default_supervisor_username: str = "supervisor"
    default_supervisor_password: str = "Supervisor@123456"
    demo_device_code: str = "CAM-01"
    demo_device_name: str = "بوابة الشمال"
    demo_device_token: str = "stvis-device-demo-token"

    @staticmethod
    def _resolve_existing_path(raw_value: str) -> str:
        path = Path(raw_value)
        if path.is_absolute():
            return str(path)

        project_root = Path(__file__).resolve().parents[3]
        candidates = [
            Path.cwd() / path,
            Path.cwd().parent / path,
            project_root / path,
        ]
        for candidate in candidates:
            if candidate.exists():
                return str(candidate.resolve())
        return str((project_root / path).resolve())

    @field_validator("debug", mode="before")
    @classmethod
    def normalize_debug_flag(cls, value):
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in {"1", "true", "yes", "debug", "development"}:
                return True
            if lowered in {"0", "false", "no", "release", "production"}:
                return False
        return bool(value)

    @field_validator("violation_model_path", "plate_model_path", mode="after")
    @classmethod
    def normalize_model_paths(cls, value: str) -> str:
        return cls._resolve_existing_path(value)

    @property
    def allowed_image_types(self) -> set[str]:
        return {item.strip() for item in self.allowed_image_mime_types.split(",") if item.strip()}

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
