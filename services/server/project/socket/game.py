from flask_socketio import emit, join_room

from project.manage import sio


@sio.on('join')
def on_join(data):
    room = data.get("room")
    join_room(room)


@sio.on("placeTile")
def on_place_tile(data):
    room = data.get("room")

    emit("placeTile", data.get("data"), json=True, room=room, include_self=False)


@sio.on("pickupTile")
def on_pickup_tile(data):
    room = data.get("room")

    emit("pickupTile", data.get("data"), json=True, room=room, include_self=False)


@sio.on("mouseHover")
def on_mouse_hover(data):
    room = data.get("room")

    emit("mouseHover", data.get("data"), json=True, room=room, include_self=False)


@sio.on("chatMessage")
def on_chat(data):
    room = data.get("room")

    print("Emitting chat message to room", room)

    emit("chatMessage", data.get("data"), json=True, room=room, include_self=True)
