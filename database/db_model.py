from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    """
    Информация о пользователе, который взаимодействует с VKinder.
    Параметры из таблицы используются для поиска других пользователей.
    """

    __tablename__ = 'user'

    vk_id = Column(Integer, primary_key=True)  # ID VK, используется как ключ
    age = Column(Integer)
    gender = Column(Integer)  # 1 — женский, 2 — мужской
    city = Column(String)

    user_searches = relationship("UserSearch", back_populates="user")
    user_interests = relationship("UserInterest", back_populates="user")


class UserSearch(Base):
    """Информация о поисковых запросах пользователя."""

    __tablename__ = 'user_search'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_vk_id = Column(Integer, ForeignKey('user.vk_id'), nullable=False)
    age_from = Column(Integer)
    age_to = Column(Integer)
    gender = Column(Integer)  # 1 — женский, 2 — мужской
    city = Column(String)
    search_date = Column(DateTime, default=datetime.now)

    user = relationship("User", back_populates="user_searches")
    search_results = relationship(
        "UserSearchResult", back_populates="user_search"
    )


class Candidate(Base):
    """
    Информация о кандидатах (пользователи ВКонтакте, которые подошли
    под заданный критерий поиска).
    Если информация об одном кандидате повторяется в разных поисковых
    запросах, то она перезаписывается.
    """

    __tablename__ = 'candidate'

    vk_id = Column(Integer, primary_key=True)  # ID VK, используется как ключ
    profile_link = Column(String)  # Ссылка на профиль
    name = Column(String)          # Имя
    last_name = Column(String)     # Фамилия
    photos = Column(JSON)          # Список фото в формате JSON

    search_results = relationship(
        "UserSearchResult", back_populates="candidate"
    )
    user_interests = relationship("UserInterest", back_populates="candidate")


class UserSearchResult(Base):
    """
    Информация о результатах поисковых запросов пользователя.
    Должна быть уникальность по сочетанию user_search_id и candidate_vk_id.
    """

    __tablename__ = 'user_search_result'
    __table_args__ = (
        UniqueConstraint(
            'user_search_id', 'candidate_vk_id',
            name='uq_user_search_candidate',
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_search_id = Column(
        Integer, ForeignKey('user_search.id'), nullable=False
    )
    candidate_vk_id = Column(
        Integer, ForeignKey('candidate.vk_id'), nullable=False
    )

    user_search = relationship("UserSearch", back_populates="search_results")
    candidate = relationship("Candidate", back_populates="search_results")


class UserInterest(Base):
    """
    Информация о реакции пользователя на предложенных кандидатов.
    Должна быть уникальность по сочетанию user_vk_id и candidate_vk_id.
    """

    __tablename__ = 'user_interest'
    __table_args__ = (
        UniqueConstraint(
            'user_vk_id', 'candidate_vk_id',
            name='uq_user_candidate_interest',
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_vk_id = Column(Integer, ForeignKey('user.vk_id'), nullable=False)
    candidate_vk_id = Column(
        Integer, ForeignKey('candidate.vk_id'), nullable=False
    )
    is_viewed = Column(Boolean, default=False)  # просмотрен пользователем
    is_liked = Column(Boolean, default=False)   # добавлен в избранное

    user = relationship("User", back_populates="user_interests")
    candidate = relationship("Candidate", back_populates="user_interests")
