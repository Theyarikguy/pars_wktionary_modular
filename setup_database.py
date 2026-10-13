from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from connection import engine


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT /"pars_modular"/ "app.db"

DATABASE_URL = f"sqlite:///{DB_PATH}"

print("DB will be at:", DB_PATH)


class Base(DeclarativeBase):
    pass


def init_db() -> None:
    """
    Создание таблиц базы данных
    """
    # создаст файл app.db и все таблицы, если их нет
    Base.metadata.create_all(bind=engine)

def drop_db() -> None:
    """
    Удаление базы данных
    """
    Base.metadata.drop_all(bind=engine)