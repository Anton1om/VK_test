from functools import wraps

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import DATABASE_URL
from database.db_model import Base

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def init_db():
    """Функция инициализации БД."""
    Base.metadata.create_all(engine)


def with_session(func):
    """
    Декоратор - открывает сессию, коммитит при успехе,
    откатывает при ошибке.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        session = SessionLocal()
        try:
            result = func(session, *args, **kwargs)
            session.commit()
            return result
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    return wrapper


def with_read_session(func):
    """
    Декоратор для чтения - открывает сессию,
    дальше закрывает сессию, без коммита.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        session = SessionLocal()
        try:
            return func(session, *args, **kwargs)
        finally:
            session.close()
    return wrapper
