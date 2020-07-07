from typing import Optional

from project.database import request_session
from project.database.models import UserModel


def get_user(uid=None, name=None) -> Optional[UserModel]:
    """
    Finds user by id or name, depending on which parameters are provided.

    :param uid:
    :param name:
    :return:
    """

    db = request_session()
    sub = db.query(UserModel)

    if uid is not None:
        sub = sub.filter(UserModel.id == uid)
    elif name is not None:
        sub = sub.filter(UserModel.name == name)
    else:
        raise ValueError("`uid` and `name` cannot both be `None`.")

    return sub.one_or_none()


def expect_result(p1, p2):
    exp = (p2 - p1) / 400.0
    return 1 / ((10.0 ** exp) + 1)


def award_elo(winner_name: str, loser_name: str):
    db = request_session()

    winner = get_user(name=winner_name)
    loser = get_user(name=loser_name)

    result = expect_result(winner.elo, loser.elo)

    winner.elo = winner.elo + 20 * (1 - result)
    loser.elo = loser.elo - 20 * (1 - result)

    # Update the values.
    db.commit()

