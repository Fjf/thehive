import ctypes
from ctypes import *
import os

# Load DLL and extract values for the struct initialization.
from project.database import user_service, db
from project.database.models import UserModel, ResultModel
from project.manage import app

filename = "libhive"
file = os.path.join(os.getcwd(), "services", "server", "project", "game", filename)
lib = CDLL(file)
board_size = c_uint.in_dll(lib, "pboardsize").value
tile_stack_size = c_uint.in_dll(lib, "ptilestacksize").value
max_turns = c_uint.in_dll(lib, "pmaxturns").value

TYPE_MASK = (1 << 5) - 1
COLOR_MASK = (1 << 5)
NUMBER_MASK = (3 << 6)
PLAYER_WHITE = (0 << 5)
PLAYER_BLACK = (1 << 5)


class Directions:
    TOP_LEFT = 0
    TOP_RIGHT = 1
    LEFT = 2
    RIGHT = 3
    BOTTOM_LEFT = 4
    BOTTOM_RIGHT = 5
    UP = 6


class TileStack(Structure):
    _fields_ = [
        ('type', c_ubyte),
        ('location', c_int),
        ('z', c_ubyte)
    ]


class Tile(Structure):
    _fields_ = [
        ('free', c_bool),
        ('type', c_ubyte)
    ]


class Player(Structure):
    _fields_ = [
        ('beetles_left', c_ubyte),
        ('grasshoppers_left', c_ubyte),
        ('queens_left', c_ubyte),
        ('ants_left', c_ubyte),
        ('spiders_left', c_ubyte)
    ]


class Board(Structure):
    _fields_ = [
        ('tiles', Tile * board_size * board_size),
        ('turn', c_int),
        ('players', Player * 2),

        ('light_queen_position', c_int),
        ('dark_queen_position', c_int),

        ('min_x', c_int),
        ('min_y', c_int),
        ('max_x', c_int),
        ('max_y', c_int),

        ('n_stacked', c_byte),
        ('stack', TileStack * tile_stack_size),

        ('move_location_tracker', c_int),

        ('zobrist_hash', c_longlong),
        ('hash_history', c_longlong * max_turns),

        ('has_updated', c_bool),
    ]


class List(Structure):
    pass


List._fields_ = [
    ('head', POINTER(List)),
    ('next', POINTER(List)),
    ('prev', POINTER(List)),
]


class MMData(Structure):
    _fields_ = [
        ('mm_value', c_float),
    ]


class Move(Structure):
    _fields_ = [
        ('tile', c_ubyte),
        ('next_to', c_ubyte),
        ('direction', c_ubyte),
        ('previous_location', c_int),
        ('location', c_int),
    ]

    def __repr__(self):
        return "%d (%d) -> (%d)" % (self.tile, self.previous_location, self.location)


#
# The PlayerArguments structure is used to specify to MCTS or Minimax what parameters to use in the search.
# Algorithm can be between 0 and 3;
#   0 - Minimax
#   1 - MCTS
#   2 - Random
#   3 - Manual
# MCTS constant is the constant used for UCB1 to define the exploration factor.
# Time to move is the amount of allotted time to select a move.
# Prioritization is an MCTS playout prioritization strategy to reduce the amount of draws.
# First play urgency is an MCTS enhancement to quickly identify good branches early on.
# Verbose generates more output per algorithm.
# Evaluation function is a switch case for Minimax, it can be 0 or 1;
#   0 - Queen surrounding prioritization
#   1 - Opponent tile blocking prioritization
#
class PlayerArguments(Structure):
    _fields_ = [
        ('algorithm', c_int),
        ('mcts_constant', c_double),
        ('time_to_move', c_double),
        ('prioritization', c_bool),
        ('first_play_urgency', c_bool),
        ('verbose', c_bool),
        ('evaluation_function', c_int),
    ]


#
# The Arguments structure stored for each player what algorithm they use and what parameters to use for this algorithm.
#
class Arguments(Structure):
    _fields_ = [
        ('p1', PlayerArguments),
        ('p2', PlayerArguments),
    ]


class Node(Structure):
    _fields_ = [
        ('children', List),
        ('node', List),
        ('move', Move),
        ('board', POINTER(Board)),
        ('data', c_uint)
    ]

    def print(self):
        lib.print_board(self.board)


TTI = [
    None,
    "ant",
    "grasshopper",
    "beetle",
    "spider",
    "queen"
]

ITT = {
    "ant": 1,
    "grasshopper": 2,
    "beetle": 3,
    "spider": 4,
    "queen": 5
}


def type_to_image(type):
    return TTI[type]


class Hive:
    def __init__(self, room_name):
        # Set return types for all functions we're using here.
        lib.game_init.restype = POINTER(Node)
        lib.list_get_node.restype = POINTER(Node)
        lib.default_init.restype = POINTER(Node)
        lib.init_board.restype = POINTER(Board)
        lib.performance_testing.restype = ctypes.c_int
        lib.finished_board.restype = ctypes.c_int

        self.board_size = board_size
        self.room_name = room_name

        # Only players can do actions
        self.players = []
        self.player_limit = 2
        if "CPU" in room_name:
            self.player_limit = 1

        # Spectators can see all actions (all players are also spectators)
        self.spectators = []

        # TODO: Only initialize certain data structures once.
        self.node = lib.game_init()

    def generate_moves(self):
        lib.generate_moves(self.node)

    def get_valid_moves(self):
        for child in self.children():
            child.print()

    def n_children(self):
        if self.node.contents.board.contents.move_location_tracker == 0:
            self.generate_moves()
        return self.node.contents.board.contents.move_location_tracker

    def print(self):
        self.node.contents.print()

    def children(self):
        """
        A generator returning child pointers
        :return:
        """
        if self.node.contents.board.contents.move_location_tracker == 0:
            self.generate_moves()

        head = self.node.contents.children.next

        while ctypes.addressof(head.contents) != ctypes.addressof(self.node.contents.children.head):
            # Get struct offset
            child = lib.list_get_node(head)

            yield child

            head = head.contents.next

    def reinitialize(self):
        # Cleanup old node
        lib.node_free(self.node)

        node = lib.default_init()
        self.node = node
        self.node.contents.board = lib.init_board()

    def select_child(self, child_num):
        """
        Returns true if this child could be removed.
        :param child_num:
        :return:
        """
        if child_num < 0 or child_num > self.node.contents.board.contents.move_location_tracker:
            return False

        for c, child in enumerate(self.children()):
            if c == child_num:
                lib.list_remove(byref(child.contents.node))
                lib.node_free(self.node)
                self.node = child
                return True
        return False

    def export(self):
        tiles = []
        for y, row in enumerate(self.node.contents.board.contents.tiles):
            tr = []
            for x, tile in enumerate(row):
                ts = []
                for stack in self.node.contents.board.contents.stack:
                    if stack.location == y * board_size + x:
                        ts.insert(stack.z, {
                            "image": type_to_image((stack.type & TYPE_MASK)),
                            "color": (stack.type & COLOR_MASK) >> 5,
                            "number": (stack.type & NUMBER_MASK) >> 6,
                            "free": False
                        })

                ts.append({
                    "image": type_to_image((tile.type & TYPE_MASK)),
                    "color": (tile.type & COLOR_MASK) >> 5,
                    "number": (tile.type & NUMBER_MASK) >> 6,
                    "free": tile.free
                })

                tr.append(ts)
            tiles.append(tr)

        return tiles

    def add_user(self, user: UserModel):
        t = "spectator"
        if len(self.players) < self.player_limit:
            self.players.append(user)
            if self.player_limit == 1:
                # Add bot if this is a bot room
                bot = UserModel(name="CPU")
                bot.id = -1
                self.players.append(bot)
                self.spectators.append(bot)
                t = "player"
        self.spectators.append(user)
        return t

    def get_player(self, username):
        for player in self.players:
            if player.name == username:
                return player

    def remove_user(self, username):
        user = user_service.get_user(username)
        if user in self.players:
            self.players.remove(user)

        self.spectators.remove(user)

    def finished(self):
        return lib.finished_board(self.node.contents.board)

    def reset_game(self):
        self.players = list(reversed(self.players))

        # Cleanup old node
        lib.node_free(self.node)
        node = lib.default_init()
        self.node = node
        self.node.contents.board = lib.init_board()

    def finalize_and_reset(self):
        from project.manage import sio
        from project.game_socket.game import system_chat, update_userlist

        room = self.room_name

        result = self.finished()

        session = db.session()
        session.add(ResultModel(self.players[0].name, self.players[1].name, result))
        session.commit()

        if result == 3:
            # Its a draw.
            sio.emit("finished", {"winner": "None", "loser": "None"}, json=True, room=room, include_self=True)
        else:
            winner = self.players[result - 1].name
            loser = self.players[result % 2].name
            sio.emit("finished", {"winner": winner, "loser": loser}, json=True, room=room, include_self=True)

            if "CPU" not in self.room_name:
                user_service.award_elo(winner, loser)

            system_chat("%s has won! Resetting the game." % winner, room=room)
            self.reset_game()

            if "CPU" in self.room_name and self.players[0].name == "CPU":
                app.bot.queue.put(room)

            update_userlist(room)

    def can_move(self, x, y):
        """
        Checks if the tile at x, y can be moved (if a tile exists at x, y)
        :param x:
        :param y:
        :return:
        """
        # Update the free property for all tiles.
        lib.update_can_move(
            self.node.contents.board,
            self.node.contents.move.location,
            self.node.contents.move.previous_location
        )

        tile = self.node.contents.board.contents.tiles[y][x]
        if tile.type == 0:
            return False

        return tile.free

    def export_tile_amounts(self, user: UserModel):
        uid = -1
        for i, player in enumerate(self.players):
            if player.name == user.name:
                uid = i
        if uid == -1:
            return None

        p = self.node.contents.board.contents.players[uid]
        return [
            {"name": "queen", "amount": p.queens_left},
            {"name": "spider", "amount": p.spiders_left},
            {"name": "beetle", "amount": p.beetles_left},
            {"name": "grasshopper", "amount": p.grasshoppers_left},
            {"name": "ant", "amount": p.ants_left},
        ]

    def export_valid_moves(self, x, y, user: UserModel):
        """
        Returns a list of all x,y coordinates the tile at x,y can move to.
        If this tile cannot be moved, this function returns an empty list.

        :param x:
        :param y:
        :param user:
        :return:
        """
        if not self.can_move(x, y):
            return []

        tile = self.node.contents.board.contents.tiles[y][x].type
        white = tile & COLOR_MASK == PLAYER_WHITE

        # Check if this tile is a white tile, and the player is player black, or vice versa
        if white and user == self.players[1] or not white and user == self.players[0]:
            # You cannot move a tile which is not your color
            return []

        positions = []
        for child in self.children():
            if child.contents.move.tile == tile:
                dx, dy = child.contents.move.location % board_size, child.contents.move.location // board_size
                positions.append((dx, dy))
        return positions

    def is_turn(self, user):
        """
        Check if the given user is to-move.
        :param user:
        :return:
        """
        to_move = self.node.contents.board.contents.turn % 2
        return self.players[to_move].name == user.name

    def get_user_list(self):
        result = []
        for user in self.spectators:
            user_type = "Spectator"
            for i, player in enumerate(self.players):
                if user.name == player.name:
                    user_type = "White" if i == 0 else "Black"
            elem = user.to_json()
            elem.update({
                "type": user_type
            })
            result.append(elem)
        return result

    def move(self, data):
        x = int(data.get("new_x"))
        y = int(data.get("new_y"))

        original_x = data.get("x", None)
        if original_x is not None:
            original_y = data.get("y")
            previous_location = int(original_y) * board_size + int(original_x)
        else:
            previous_location = -1

        location = y * board_size + x

        # Placing the tile back on the original position is valid, and will not use up a turn.
        if previous_location == location:
            return 1

        if self.node.contents.board.contents.turn == 0:
            location = (board_size // 2) * board_size + (board_size // 2)
        if self.node.contents.board.contents.turn == 1:
            location = (board_size // 2) * board_size + (board_size // 2) + 1

        # Select the child with the same move as proposed
        for i, child in enumerate(self.children()):
            tile_type = TTI[child.contents.move.tile & TYPE_MASK]
            if child.contents.move.location == location \
                    and child.contents.move.previous_location == previous_location \
                    and data.get("image") == tile_type:
                self.select_child(i)
                return 2

        return 0

    def ai_move(self, algorithm_type):
        if algorithm_type == "minimax":
            pa = PlayerArguments()
            pa.time_to_move = 2
            pa.verbose = False
            pa.evaluation_function = 3  # Current best version
            lib.minimax(pointer(self.node), pa)

# h = Hive()
# p1 = UserModel("Test")
# p2 = UserModel("Test2")
# h.add_user(p1)
# h.add_user(p2)
#
# for i in range(10):
#     h.generate_moves()
#     h.select_child(random.randint(0, h.n_children() - 1))
#
# prev = h.node.contents.move.location
# h.print()
# x, y = prev % board_size, prev // board_size
# h.export_valid_moves(x, y, p2)
#
# exit(1)
