from project.game.Player import Player


class TileTypes:
    DEFAULT = 0
    QUEEN = 1
    GRASSHOPPER = 2
    ANT = 3
    SPIDER = 4
    BEETLE = 5
    LADYBUG = 6
    MOSQUITO = 7


class Tile:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.type = TileTypes.DEFAULT


def positive_mod(y, mod):
    return ((y % mod) + mod) % mod


class Board:
    def __init__(self):
        self.tiles = {}
        self.players = []
        self.turn = 0
        self.turn_number = 0

    def is_turn(self, player: Player):
        if self.players[self.turn] == player:
            return True
        return False

    def next_turn(self):
        # Do round-robin selection of turns
        self.turn = (self.turn + 1) % len(self.players)
        self.turn_number += 1

    def get_hive_squares(self):
        """
        Returns all valid squares around, and in the hive

        :return:
        """
        hive_tiles = []
        return hive_tiles

    def move(self, original_tile: Tile, new_tile: Tile):
        """
        Attempts to move the original tile to the new tile location.
        If it succeeds, returns True, otherwise False

        :param original_tile:
        :param new_tile:
        :return:
        """
        if self.turn_number == 0:
            return True
        elif self.turn_number == 1:
            # In turn two, the first tile must have been placed already.
            tile = list(list(self.tiles.values())[0].values())[0]
            return self.get_tiles_around(tile)

        moves = self.get_valid_moves(original_tile)

        for move in moves:
            if new_tile.x == move.x and new_tile.y == move.y:
                # TODO: Do the actual move
                return True

        return False

    def get_valid_moves(self, original_tile):
        valid_moves = self.get_hive_squares()

        # Newly placed tile on the board
        if original_tile is None:
            valid_moves = self.get_allied_squares(valid_moves)
            pass
        # Move a tile from the original tile location to the new tile location.
        else:
            if original_tile.type == TileTypes.ANT:
                valid_moves = self.get_valid_ant_moves(valid_moves)

            if original_tile.type == TileTypes.QUEEN:
                valid_moves = self.get_valid_queen_moves(valid_moves)

            if original_tile.type == TileTypes.GRASSHOPPER:
                valid_moves = self.get_valid_grasshopper_moves(valid_moves)

        return valid_moves

    def get_allied_squares(self, subset=None) -> list:
        if subset is None:
            subset = []

        pass

    def get_valid_grasshopper_moves(self, position, subset=None):
        if subset is None:
            subset = []

    def get_valid_queen_moves(self, position, subset=None):
        if subset is None:
            subset = []

    def get_valid_ant_moves(self, position, subset=None):
        if subset is None:
            subset = []

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
