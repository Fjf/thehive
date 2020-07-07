from typing import Optional

from flask import session

from flask import session, g as flaskg

from project.database import user_service
from project.database.models import UserModel


def session_user() -> UserModel:
    """
    Return the currently authenticated user.
    :return: the currently authenticated user.
    :raises: ValueError if no user is logged in.
    """

    user_id = session['user_id'] if 'user_id' in session else None
    if user_id is not None:
        if not hasattr(flaskg, 'session_user'):
            flaskg.session_user = user_service.get_user(uid=user_id)

            if flaskg.session_user is None:
                del session['user_id']

        return flaskg.session_user
    raise ValueError('No user logged in.')


def session_user_set(user: Optional[UserModel]):
    """
    Set the current user associated with the session.

    :param user: The user or None.
    """

    if user is None:
        del session['user_id']
    else:
        session['user_id'] = user.id
