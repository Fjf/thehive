import bcrypt as bcrypt
from sqlalchemy import Column, Integer, LargeBinary, String, Float
from sqlalchemy.orm import deferred

from project.database import OrmModelBase


class UserModel(OrmModelBase):
    """
    A user model also containing the elo for matchmaking points.
    """

    __tablename__ = 'users'

    id = Column(Integer(), primary_key=True, autoincrement=True)

    name = Column(String(), unique=True, nullable=False)
    password = deferred(Column(LargeBinary(), nullable=False))

    elo = Column(Float(), unique=False, default=1200)

    def __init__(self, name: str, password: str = None):
        self.name = name
        if password is not None:
            self.password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

    def check_password(self, password):
        return bcrypt.checkpw(password.encode(), self.password)

    def to_json(self):
        return {
            "id": self.id,
            "name": self.name,
            "elo": self.elo
        }
