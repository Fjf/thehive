import ctypes
import random
from ctypes import *
import os

# Load DLL and extract values for the struct initialization.
from project.database import user_service
from project.database.models import UserModel

filename = "libhive"
file = os.path.join(os.getcwd(), "services", "server", "project", "game", filename)
print(file)
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
        ('tile', c_byte),
        ('next_to', c_byte),
        ('direction', c_byte),
        ('previous_location', c_int),
        ('location', c_int),
    ]


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


class Hive:
    def __init__(self):
        # Set return types for all functions we're using here.
        lib.game_init.restype = POINTER(Node)
        lib.list_get_node.restype = POINTER(Node)
        lib.default_init.restype = POINTER(Node)
        lib.init_board.restype = POINTER(Board)
        lib.performance_testing.restype = ctypes.c_int
        lib.finished_board.restype = ctypes.c_int

        # Only players can do actions
        self.players = []
        self.player_limit = 2
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
        tiles = [[{"type": (t.type & TYPE_MASK),
                   "color": (t.type & COLOR_MASK) >> 5,
                   "number": (t.type & NUMBER_MASK) >> 6,
                   "free": t.free} for t in row] for row in self.node.contents.board.contents.tiles]
        for t in tiles:
            print(t)

        return tiles

    def add_user(self, user: UserModel):
        if len(self.players) < self.player_limit:
            self.players.append(user)
        self.spectators.append(user)

    def remove_user(self, username):
        user = user_service.get_user(username)
        if user in self.players:
            self.players.remove(user)

        self.spectators.remove(user)

    def get_player(self, username):
        user = user_service.get_user(username)
        if user in self.players:
            return user

    def finished(self):
        return lib.finished_board(self.node.contents.board)

    def reset_game(self):
        # Cleanup old node
        lib.node_free(self.node)
        node = lib.default_init()
        self.node = node
        self.node.contents.board = lib.init_board()

    def can_move(self, x, y):
        """
        Checks if the tile at x, y can be moved (if a tile exists at x, y)
        :param x:
        :param y:
        :return:
        """
        tile = self.node.contents.board.contents.tiles[y * board_size + x]
        if tile.type == 0:
            return False
        return tile.free

    def export_valid_moves(self, x, y, user):
        if not self.can_move(x, y):
            return False

        tile = self.node.contents.board.contents.tiles[y * board_size + x]
        white = tile & COLOR_MASK == PLAYER_WHITE
        # Check if this tile is a white tile, and the player is player black, or vice versa
        if white and user == self.players[1] or not white and user == self.players[0]:
            # You cannot move a tile which is not your color
            return False

    def is_turn(self, user):
        """
        Check if the given user is to-move.
        :param user:
        :return:
        """
        to_move = self.node.contents.board.contents.turn % 2
        return self.players[to_move] == user
