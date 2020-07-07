from flask import request
from werkzeug.exceptions import Conflict, NotFound

from project.api import api
from project.database import user_service, request_session
from project.database.models import UserModel
from project.session import session_user_set


@api.route("users/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    user = user_service.get_user(name=username)
    if user is None:
        return NotFound("This username cannot be found.")

    if user.check_password(password):
        session_user_set(user)
        return user.to_json()


@api.route("users/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    user = user_service.get_user(name=username)
    if user is not None:
        raise Conflict("This username already exists.")

    user = UserModel(username, password)

    db = request_session()
    db.add(user)
    db.commit()

    session_user_set(user)
    return user.to_json()


@api.route("users/logout", methods=["POST"])
def logout():
    session_user_set(None)


print("Finished loading user.py api routes.")