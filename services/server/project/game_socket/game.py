import inspect
import json

from flask_socketio import emit, join_room, leave_room

from project.database import user_service
from project.game.Board import Hive
from project.manage import sio, app
from project.session import session_user


class ObjectEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, "to_json"):
            return self.default(obj.to_json())
        elif hasattr(obj, "__dict__"):
            d = dict(
                (key, value)
                for key, value in inspect.getmembers(obj)
                if not key.startswith("_")
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


def system_chat(text, room=None):
    if room is None:
        sio.emit("chatMessage", {
            "name": "SYSTEM",
            "message": text
        }, json=True, include_self=True)
    else:
        sio.emit("chatMessage", {
            "name": "SYSTEM",
            "message": text
        }, json=True, include_self=True, room=room)


@sio.on("join")
def on_join(data):
    user = session_user()
    if user is None:
        return

    room = data.get("room")
    join_room(room)

    if room not in app.games:
        app.games[room] = Hive(room)

    game = app.games[room]

    update_board(room)

    # The player has already joined.
    if user.name not in [s.name for s in game.spectators]:
        # Adds the current player to the room as either spectator or player depending on if they are quick enough.
        player_type = game.add_user(user)
        system_chat("%s has joined as %s" % (user.name, player_type), room=room)

    # Update everybody's player and spectator list.
    update_userlist(room)

    if user is not None:
        emit("tileAmounts", game.export_tile_amounts(user), json=True, include_self=True)


def update_userlist(room):
    sio.emit("userList", app.games[room].get_user_list(), json=True, room=room, include_self=True)


def update_board(room, to_room=False):
    if room not in app.games:
        return

    game = app.games[room]
    board_state = json.dumps(game.export())
    if to_room:
        sio.emit("boardState", board_state, json=True, include_self=True, room=room)
    else:
        sio.emit("boardState", board_state, json=True, include_self=True)


@sio.on("leave")
def on_leave(data):
    room = data.get("room")

    username = data.get("username")

    system_chat("%s left the room." % username, room=room)

    if app.games[room].get_player(username):
        app.games[room] = Hive(room)
        system_chat(
            "Because %s has left the room, game has been reset. Please rejoin the room to start a new game." % username,
            room=room)
    else:
        app.games[room].remove_user(username)

    update_userlist(room)
    leave_room(room)


@sio.on("getBoard")
def on_get_board(request):
    room = request.get("room")
    update_board(room, to_room=False)


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
    username = request.get("username")
    data = request.get("data")
    game = app.games[room]

    # if len(game.players) < game.player_limit:
    #     system_chat("Game is not yet ready to start.")
    #     return

    user = session_user()
    if not game.is_turn(user):
        system_chat("It is not yet your turn.")
        return

    result = game.move(data)
    if result == 2:
        x = game.node.contents.move.location % game.board_size
        y = game.node.contents.move.location / game.board_size
        emit("placeTile", {
            "username": username,
            "x": x,
            "y": y,
        }, json=True, room=room, include_self=True)

        # Update userlist with new active player turn.
        update_userlist(room)

        result = game.finished()
        if result > 0:
            game.finalize_and_reset()
        else:
            if "CPU" in room:
                # app.games[room].ai_move("minimax")
                app.bot.queue.put(room)
    elif result == 1:
        response = {
            "username": username
        }
        emit("placeTile", response, json=True, room=room, include_self=True)

    update_board(room, to_room=True)
    emit("tileAmounts", game.export_tile_amounts(user), json=True, include_self=True)

    if game.n_children() == 0:
        system_chat("There are no moves left, skipping this turn.", room=room)
        game.node.contents.board.contents.turn += 1


@sio.on("pickupTile")
def on_pickup_tile(request):
    user = session_user()
    room = request.get("room")
    data = request.get("data")

    game = app.games[room]

    if not game.is_turn(user):
        system_chat("It is not yet your turn.")
        return

    x = int(data.get("x"))
    y = int(data.get("y"))
    if not game.can_move(x, y):
        system_chat("Cannot move tile at %d, %d" % (x, y))
        return

    # Send available tiles
    moves = game.export_valid_moves(x, y, user)
    markings = json.dumps(moves)
    emit("markedTiles", markings, json=True, include_self=True)
    emit("pickupTile", request, json=True, room=room, include_self=True)


@sio.on("mouseHover")
def on_mouse_hover(data):
    room = data.get("room")
    username = data.get("username")

    if room not in app.games:
        return

    game = app.games[room]

    for player in game.players:
        if player.name == username:
            emit("mouseHover", data, json=True, room=room, include_self=False)
            return


@sio.on("chatMessage")
def on_chat(data):
    room = data.get("room")

    emit("chatMessage", data.get("data"), json=True, room=room, include_self=True)
