import _thread
import inspect
import json
from collections import defaultdict

from flask_socketio import emit, join_room, leave_room

from project.database import user_service
from project.database.models import UserModel
from project.game.Board import Board
from project.manage import sio
from project.session import session_user

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


def system_chat(text, room=None):
    if room is None:
        emit("chatMessage", {
            "name": "SYSTEM",
            "message": text
        }, json=True, include_self=True)
    else:
        emit("chatMessage", {
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

    game = games[room]
    username = user.name

    update_board(room)

    # The player has already joined.
    if game.get_player(username) is None:
        # Adds the current player to the room as either spectator or player depending on if they are quick enough.
        player_type = game.add_player(user)
        system_chat("%s has joined as %s" % (user.name, player_type), room=room)

    # Update everybody's player and spectator list.
    update_userlist(room)

    # Send the joined user his remaining tiles
    player = game.get_player(username)
    if player is not None:
        emit("tileAmounts", player.get_tile_amounts(), json=True, include_self=True)


def update_userlist(room):
    emit("userList", games[room].get_player_list(), json=True, room=room, include_self=True)


def update_board(room, to_room=False):
    game = games[room]
    board_state = json.dumps(game.tiles, cls=ObjectEncoder)
    if to_room:
        emit("boardState", board_state, json=True, include_self=True, room=room)
    else:
        emit("boardState", board_state, json=True, include_self=True)


@sio.on("leave")
def on_leave(data):
    room = data.get("room")

    username = data.get("username")

    system_chat("%s left the room." % username, room=room)

    if games[room].get_player(username) is not None:
        games[room] = Board()
        system_chat(
            "Because %s has left the room, game has been reset. Please rejoin the room to start a new game." % username,
            room=room)
    else:
        games[room].remove_player(username)

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
    game = games[room]

    # Dont allow moves if the game has finished.
    if game.winner is not None:
        system_chat("The game has already finished.")
        return

    if len(game.players) < game.max_players:
        system_chat("Game is not yet ready to start.")
        return

    user = game.get_player(username)
    if not game.is_turn(user):
        system_chat("It is not yet your turn.")
        return

    if game.move(user, data):
        x = int(data.get("new_x"))
        y = int(data.get("new_y"))

        tile = game.get_tile(x, y)
        response = {
            "username": username,
            "data": {
                "x": tile.x,
                "y": tile.y,
                "z": tile.z,
                "image": data.get("image")
            }
        }

        emit("placeTile", response, json=True, room=room, include_self=True)
        # Update userlist with new active player turn.
        update_userlist(room)

        if game.finished():
            emit("finished", {"winner": game.winner, "loser": game.loser}, json=True, room=room, include_self=True)

            user_service.award_elo(game.winner, game.loser)

            system_chat("%s has won! Resetting the game." % game.winner, room=room)
            game.reset_game()

            update_board(room, to_room=True)
            update_userlist(room)
        else:
            if "CPU" in room:
                cpu = game.get_turn()
                _thread.start_new_thread(do_cpu_move, (game, cpu, room))


def do_cpu_move(game, cpu, room):
    # move = select_move(game, cpu)
    # game.move(cpu, move)
    pass


@sio.on("pickupTile")
def on_pickup_tile(request):
    room = request.get("room")
    username = request.get("username")
    data = request.get("data")

    game = games[room]

    # Dont allow moves if the game has finished.
    if game.winner is not None:
        system_chat("The game has already finished.")
        return

    user = game.get_player(username)
    if not game.is_turn(user):
        system_chat("It is not yet your turn.")
        return

    x = int(data.get("x"))
    y = int(data.get("y"))
    tile = game.get_tile(x, y)
    if tile is None:
        system_chat("There is no tile on (%d, %d) to pick up." % (x, y))
        return

    if game.breaks_hive(tile):
        system_chat("This move would break the hive.")
        return

    # Send available tiles
    markings = json.dumps(list(game.export_valid_moves(x, y, user)), cls=ObjectEncoder)
    emit("markedTiles", markings, json=True, include_self=True)
    emit("pickupTile", request, json=True, room=room, include_self=True)


@sio.on("mouseHover")
def on_mouse_hover(data):
    room = data.get("room")
    username = data.get("username")

    game = games[room]

    for player in game.players:
        if player.user.name == username:
            emit("mouseHover", data, json=True, room=room, include_self=False)
            return


@sio.on("chatMessage")
def on_chat(data):
    room = data.get("room")

    emit("chatMessage", data.get("data"), json=True, room=room, include_self=True)
