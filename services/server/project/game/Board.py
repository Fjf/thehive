import json
from collections import defaultdict
from typing import Optional

from project.game.Player import Player


class Tile:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.owner = None
        self.type = "unknown"

    def __repr__(self):
        return json.dumps(self.__dict__)

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y and self.owner == other.owner and self.type == other.type

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self.x, self.y, self.owner, self.type))


def positive_mod(y, mod):
    return ((y % mod) + mod) % mod


def position_in_list(new_tile, tiles):
    for tile in tiles:
        if tile.x == new_tile.x and tile.y == new_tile.y:
            return True
    return False


class Board:
    def __init__(self):
        self.tiles = defaultdict(dict)
        self.players = []
        self.spectators = []
        self.max_players = 2
        self.turn = 0
        self.turn_number = 0

    def add_player(self, name: str):
        if len(self.players) < self.max_players:
            self.players.append(name)
            return "player"
        else:
            self.spectators.append(name)
            return "spectator"

    def is_turn(self, player: Player):
        if self.players[self.turn] == player:
            return True
        return False

    def next_turn(self):
        # Do round-robin selection of turns
        self.turn = (self.turn + 1) % len(self.players)
        self.turn_number += 1

    def get_hive_tiles(self, exclude=None) -> set:
        """
        Returns all valid squares around, and in the hive

        :return:
        """
        hive_tiles = set()
        for y, row in self.tiles.items():
            for x, tile in row.items():
                if exclude is not None and x == exclude.x and y == exclude.y:
                    continue
                around = set(self.get_tiles_around(tile))
                hive_tiles = hive_tiles.union(around)

        return hive_tiles

    def is_move_valid(self, original_tile: Optional[Tile], new_tile: Tile, user: str):
        """
        Attempts to move the original tile to the new tile location.
        If it succeeds, returns True, otherwise False

        :param user:
        :param original_tile:
        :param new_tile:
        :return:
        """
        if self.turn_number == 0:
            return True
        elif self.turn_number == 1:
            # In turn two, the first tile must have been placed already.
            tile = list(list(self.tiles.values())[0].values())[0]
            return position_in_list(new_tile, self.get_tiles_around(tile))

        moves = self.get_valid_moves(original_tile, user)
        return position_in_list(new_tile, moves)

    def get_valid_moves(self, original_tile, user):
        valid_moves = self.get_hive_tiles(original_tile)

        # Newly placed tile on the board
        if original_tile is None:
            valid_moves = self.get_allied_squares(valid_moves, user)

        # Move a tile from the original tile location to the new tile location.
        else:
            if original_tile.type == "ant":
                valid_moves = self.get_valid_ant_moves(original_tile, valid_moves)

        return valid_moves

    def get_allied_squares(self, subset: set, user: str) -> set:
        result = set()

        for entry in subset:
            selection = self.get_tile(entry.x, entry.y)

            # Allied squares must be empty, as you cannot initially place tiles on top of another.
            if selection is not None:
                continue

            selection = Tile(entry.x, entry.y)

            surroundings = set(self.get_tiles_around(selection))
            for surrounding in surroundings:
                tile = self.get_tile(surrounding.x, surrounding.y)
                if tile is not None and tile.owner == user:
                    result.add(selection)

        return result

    def get_valid_grasshopper_moves(self, position, subset):
        result = set()



        return result

    def get_valid_queen_moves(self, position, subset):
        result = set()

        return result

    def get_valid_ant_moves(self, position, subset):
        """
        Ants may only move to unoccupied spaces.

        :param position:
        :param subset:
        :return:
        """
        result = set()

        for entry in subset:
            tile = self.get_tile(entry.x, entry.y)

            if tile is None:
                result.add(Tile(entry.x, entry.y))

        return result

    def get_tiles_around(self, tile: Tile):
        bump = positive_mod(tile.y, 2) * 2 - 1

        tiles = [
            # Add top and bottom
            Tile(tile.x, tile.y - 1),
            Tile(tile.x, tile.y + 1),
            # Add left and right
            Tile(tile.x - 1, tile.y),
            Tile(tile.x + 1, tile.y),
            # Add the other two up and down tiles
            Tile(tile.x + bump, tile.y - 1),
            Tile(tile.x + bump, tile.y + 1)
        ]

        return tiles

    def get_tile(self, x: int, y: int) -> Optional[Tile]:
        if x in self.tiles[y]:
            return self.tiles[y][x]
        return None

    def put_tile(self, tile):
        self.tiles[tile.y][tile.x] = tile

    def move(self, user, data):
        x = data.get("new_x")
        y = data.get("new_y")
        original_x = data.get("x", None)
        original_y = data.get("y", None)

        tile = Tile(x, y)
        tile.owner = user
        tile.type = data.get("image")

        original_tile = None
        if original_x is not None:
            original_tile = self.get_tile(original_x, original_y)

        if self.is_move_valid(original_tile, tile, user):
            # Remove tile on previous location
            if original_tile is not None:
                print("deleting", original_tile.x, original_tile.y)
                del self.tiles[original_tile.y][original_tile.x]

            self.put_tile(tile)
            self.next_turn()
            print(self.tiles)
            return True

        return False
