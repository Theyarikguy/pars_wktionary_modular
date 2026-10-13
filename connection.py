from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import settings

from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import settings

engine = create_engine(
    settings.DATABASE_URL,
    echo=False,  # для отладки SQL-запросов
    future=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db():
    """
    Аналог FastAPI-зависимости get_db для использования вне веб-приложения.

    Использование:
        with get_db() as db:
            db.add(obj)

    Автоматически коммитит при успехе, откатывает при исключении
    и всегда закрывает сессию.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()