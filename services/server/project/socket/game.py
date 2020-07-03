import inspect
import json
from collections import defaultdict

from flask_socketio import emit, join_room

from project.game.Board import Board
from project.manage import sio

games = defaultdict(Board)


class ObjectEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, "to_json"):
            return self.default(obj.to_json())
        elif hasattr(obj, "__dict__"):
            d = dict(
                (key, value)
                for key, value in inspect.getmembers(obj)
                if not key.startswith("__")
                and not inspect.isabstract(value)
                and not inspect.isbuiltin(value)
                and not inspect.isfunction(value)
                and not inspect.isgenerator(value)
                and not inspect.isgeneratorfunction(value)
                and not inspect.ismethod(value)
                and not inspect.ismethoddescriptor(value)
                and not inspect.isroutine(value)
            )
            return self.default(d)
        return obj


@sio.on('join')
def on_join(data):
    room = data.get("room")
    join_room(room)

    game = games[room]
    username = data.get("username")

    emit("boardState", json.dumps(game.tiles, cls=ObjectEncoder), json=True, include_self=True)

    # The player has already joined.
    if username in games[room].players:
        return

    # Adds the current player to the room as either spectator or player depending on if they are quick enough.
    player_type = games[room].add_player(data.get("username"))

    response = {
        "name": "SYSTEM",
        "message": "%s has joined as %s" % (data.get("username"), player_type)
    }

    emit("chatMessage", response, json=True, room=room, include_self=True)


@sio.on("placeTile")
def on_place_tile(request):
    """
        Assume data to be formatted as follows;

        x
        y
        original_x
        original_y
        name
    """
    room = request.get("room")
    user = request.get("username")
    data = request.get("data")
    game = games[room]

    # if len(game.players) < game.max_players:
    #     print("Game not yet ready to start.")
    #     # TODO: Notify the player the game is not yet ready to start.
    #     return

    if not game.is_turn(user):
        # TODO: Notify the user it is not yet his turn.
        return

    print(data)

    if game.move(user, data):
        response = {
            "username": user,
            "data": {
                "x": data.get("new_x"),
                "y": data.get("new_y"),
                "image": data.get("image")
            }
        }
        emit("placeTile", response, json=True, room=room, include_self=True)


@sio.on("pickupTile")
def on_pickup_tile(request):
    room = request.get("room")
    user = request.get("username")
    data = request.get("data")

    game = games[room]
    if not game.is_turn(user):
        # TODO: Notify the user it is not yet his turn.
        return

    # emit("availablePlaces", request, json=True, room=room, include_self=True)
    emit("pickupTile", request, json=True, room=room, include_self=True)


@sio.on("mouseHover")
def on_mouse_hover(data):
    room = data.get("room")

    emit("mouseHover", data.get("data"), json=True, room=room, include_self=False)


@sio.on("chatMessage")
def on_chat(data):
    room = data.get("room")

    emit("chatMessage", data.get("data"), json=True, room=room, include_self=True)
