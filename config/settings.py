# * ==============================================================================
# *                              Settings
# * ==============================================================================

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./exam_grader.db"
    ollama_model: str = "llama3"
    ollama_base_url: str = "http://localhost:11434"

    # ? لیست origin های مجاز برای CORS - پیش‌فرض "*" (همه) چون این پروژه
    # ! فعلاً هیچ احراز هویتی ندارد و صرفاً برای دمو/مسابقه استفاده می‌شود.
    # ! قبل از استقرار واقعی (production)، این باید به دامنه دقیق Frontend
    # ! محدود شود، نه "*".
    cors_allowed_origins: list[str] = ["*"]


@lru_cache
def get_settings() -> Settings:
    # ? lru_cache یعنی Settings فقط یک‌بار خوانده می‌شود، نه در هر request
    return Settings()
