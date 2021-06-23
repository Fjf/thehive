import bcrypt as bcrypt
from sqlalchemy import Column, Integer, LargeBinary, String, Float
from sqlalchemy.orm import deferred

from project.database import Base


class UserModel(Base):
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

    def __repr__(self):
        return "%d: %s" % (self.id, self.name)


class ResultModel(Base):
    """
    A user model also containing the elo for matchmaking points.
    """

    __tablename__ = 'results'

    id = Column(Integer(), primary_key=True, autoincrement=True)

    player1 = Column(String(), unique=True, nullable=False)
    player2 = Column(String(), unique=True, nullable=False)

    result = Column(Integer(), nullable=False)

    def __init__(self, player1: str, player2: str, result: int):
        self.player1 = player1
        self.player2 = player2
        self.result = result