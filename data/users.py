import sqlalchemy
from .db_session import SqlAlchemyBase


class User(SqlAlchemyBase):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    favorites = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    last_search = sqlalchemy.Column(sqlalchemy.String, nullable=True)
