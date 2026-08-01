# * ==============================================================================
# *                          Database Session
# * ==============================================================================

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from config.settings import get_settings
from infrastructure.database.models import Base

settings = get_settings()

# ? check_same_thread=False فقط برای SQLite لازم است چون FastAPI ممکن است
# ? از thread های مختلف به session دسترسی پیدا کند.
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    # ? در فاز ۱ از create_all برای سادگی استفاده می‌کنیم؛ در آینده اگر مهاجرت
    # ? schema پیچیده شد، به Alembic مهاجرت می‌کنیم.
    Base.metadata.create_all(bind=engine)


def get_db_session() -> Generator[Session, None, None]:
    # ? این تابع به‌عنوان FastAPI dependency استفاده می‌شود تا هر request
    # ? یک session مستقل بگیرد و در پایان بسته شود.
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
