import json
from typing import Optional

from project.database.models import UserModel
from project.game.Player import Player


class Directions:
    TOP_LEFT = 0
    TOP_RIGHT = 1
    BOTTOM_LEFT = 2
    BOTTOM_RIGHT = 3
    LEFT = 4
    RIGHT = 5


class Tile:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.original_x = None
        self.original_y = None
        self.z = 0
        self.owner = None
        self.type = "unknown"

    def __repr__(self):
        return json.dumps(self.__dict__)

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y and self.owner == other.owner and self.type == other.type and self.z == other.z

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self.x, self.y, self.owner, self.type))


def positive_mod(y, mod):
    return ((y % mod) + mod) % mod


def is_in_list(new_tile, tiles):
    for tile in tiles:
        if tile.x == new_tile.x and tile.y == new_tile.y:
            return True
    return False


def _make_bottom_right(tile):
    if tile.y % 2 == 0:
        return Tile(tile.x, tile.y + 1)
    else:
        return Tile(tile.x + 1, tile.y + 1)


def _make_bottom_left(tile):
    if tile.y % 2 == 0:
        return Tile(tile.x - 1, tile.y + 1)
    else:
        return Tile(tile.x, tile.y + 1)


def _make_top_right(tile):
    if tile.y % 2 == 0:
        return Tile(tile.x, tile.y - 1)
    else:
        return Tile(tile.x + 1, tile.y - 1)


def _make_top_left(tile):
    if tile.y % 2 == 0:
        return Tile(tile.x - 1, tile.y - 1)
    else:
        return Tile(tile.x, tile.y - 1)


def _make_tiles_around(tile: Tile):
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


def get_direction(position, tile):
    if position.y == tile.y and position.x == tile.x - 1:
        return Directions.LEFT
    if position.y == tile.y and position.x == tile.x + 1:
        return Directions.RIGHT
    if (position.y % 2 == 0 and position.x - 1 == tile.x and position.y - 1 == tile.y) \
            or (position.x == tile.x and position.y - 1 == tile.y):
        return Directions.TOP_LEFT
    if (position.y % 2 == 0 and position.x == tile.x and position.y - 1 == tile.y) \
            or (position.x + 1 == tile.x and position.y - 1 == tile.y):
        return Directions.TOP_RIGHT
    if (position.y % 2 == 0 and position.x - 1 == tile.x and position.y + 1 == tile.y) \
            or (position.x == tile.x and position.y + 1 == tile.y):
        return Directions.BOTTOM_LEFT
    if (position.y % 2 == 0 and position.x == tile.x and position.y + 1 == tile.y) \
            or (position.x + 1 == tile.x and position.y + 1 == tile.y):
        return Directions.BOTTOM_RIGHT


def slow_get_direction(position, tile):
    if _make_top_left(position) == tile:
        return Directions.TOP_LEFT
    if _make_top_right(position) == tile:
        return Directions.TOP_RIGHT
    if _make_bottom_left(position) == tile:
        return Directions.BOTTOM_LEFT
    if _make_bottom_right(position) == tile:
        return Directions.BOTTOM_RIGHT
    if position.y == tile.y and position.x == tile.x - 1:
        return Directions.LEFT
    if position.y == tile.y and position.x == tile.x + 1:
        return Directions.RIGHT
    return None



class Board:
    def __init__(self):
        self.tiles = {}
        self.players = []
        self.spectators = []
        self.max_players = 2
        self.turn = 0
        self.turn_number = 0
        self.winner = None
        self.loser = None

    def add_player(self, user: UserModel):
        if len(self.players) < self.max_players:
            self.players.append(Player(self, user))
            return "player"
        else:
            self.spectators.append(Player(self, user))
            return "spectator"

    def is_turn(self, player: Player):
        if self.players[self.turn] == player:
            return True
        return False

    def get_turn(self):
        return self.players[self.turn]

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
            for x, l in row.items():
                # row.items() is a list of all tiles on a single square, while get_tile returns the highest one.
                tile = self.get_tile(x, y)

                # Skip this entry if the coordinates are the same, and if there is no tile underneath.
                if exclude is not None and x == exclude.x and y == exclude.y and len(l) == 1:
                    continue
                if tile is None:
                    continue
                around = set(_make_tiles_around(tile))
                hive_tiles = hive_tiles.union(around)

        return hive_tiles

    def is_move_valid(self, original_tile: Optional[Tile], new_tile: Tile, user: Player):
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
            tile = self._get_random_tile()
            return is_in_list(new_tile, _make_tiles_around(tile))

        moves = self.get_valid_moves(original_tile, user)
        return is_in_list(new_tile, moves)

    def _get_random_tile(self):
        for row in self.tiles.values():
            for col in row.values():
                if len(col) > 0:
                    return col[len(col) - 1]
        return None

    def _get_top_left(self, tile):
        if tile.y % 2 == 0:
            return self.get_tile(tile.x - 1, tile.y - 1)
        else:
            return self.get_tile(tile.x, tile.y - 1)

    def _get_top_right(self, tile):
        if tile.y % 2 == 0:
            return self.get_tile(tile.x, tile.y - 1)
        else:
            return self.get_tile(tile.x + 1, tile.y - 1)

    def _get_bottom_left(self, tile):
        if tile.y % 2 == 0:
            return self.get_tile(tile.x - 1, tile.y + 1)
        else:
            return self.get_tile(tile.x, tile.y + 1)

    def _get_bottom_right(self, tile):
        if tile.y % 2 == 0:
            return self.get_tile(tile.x, tile.y + 1)
        else:
            return self.get_tile(tile.x + 1, tile.y + 1)

    def get_valid_moves(self, original_tile, user: Player):
        valid_moves = self.get_hive_tiles(original_tile)

        # Newly placed tile on the board
        if original_tile is None:
            valid_moves = self.get_allied_squares(valid_moves, user)

        # Move a tile from the original tile location to the new tile location.
        else:
            # Remove the current tile so it will not be taken into account.
            excluded = self.tiles[original_tile.y][original_tile.x].pop()

            if original_tile.type == "ant":
                valid_moves = self._get_valid_ant_moves(original_tile, valid_moves)
            elif original_tile.type == "grasshopper":
                valid_moves = self._get_valid_grasshopper_moves(original_tile)
            elif original_tile.type == "queen":
                valid_moves = self._get_valid_queen_moves(original_tile, subset=valid_moves)
            elif original_tile.type == "beetle":
                valid_moves = self._get_valid_beetle_moves(original_tile, subset=valid_moves)
            elif original_tile.type == "spider":
                valid_moves = self._get_valid_spider_moves(original_tile, subset=valid_moves)
            elif original_tile.type == "mosquito":
                valid_moves = self._get_valid_mosquito_moves(original_tile, subset=valid_moves)
            elif original_tile.type == "ladybug":
                valid_moves = self._get_valid_ladybug_moves(original_tile, subset=valid_moves)

            self.put_tile(excluded)

            actual = Tile(original_tile.x, original_tile.y)
            if actual in valid_moves:
                valid_moves.remove(actual)
        return valid_moves

    def get_allied_squares(self, subset: set, player: Player) -> set:
        result = set()

        for entry in subset:
            selection = self.get_tile(entry.x, entry.y)

            # Allied squares must be empty, as you cannot initially place tiles on top of another.
            if selection is not None:
                continue

            selection = Tile(entry.x, entry.y)

            surroundings = set(_make_tiles_around(selection))
            valid = True
            for surrounding in surroundings:
                tile = self.get_tile(surrounding.x, surrounding.y)
                if tile is not None and tile.owner != player.user.name:
                    valid = False
                    break

            if valid:
                result.add(selection)

        return result

    def _get_valid_grasshopper_moves(self, position: Tile):
        result = set()

        cursor = position
        while self._get_top_left(cursor) is not None:
            cursor = self._get_top_left(cursor)
        if cursor is not position:
            result.add(_make_top_left(cursor))

        cursor = position
        while self._get_top_right(cursor) is not None:
            cursor = self._get_top_right(cursor)
        if cursor is not position:
            result.add(_make_top_right(cursor))

        cursor = position
        while self._get_bottom_left(cursor) is not None:
            cursor = self._get_bottom_left(cursor)
        if cursor is not position:
            result.add(_make_bottom_left(cursor))

        cursor = position
        while self._get_bottom_right(cursor) is not None:
            cursor = self._get_bottom_right(cursor)
        if cursor is not position:
            result.add(_make_bottom_right(cursor))

        cursor = position
        # Left horizontally
        while self.get_tile(cursor.x - 1, cursor.y) is not None:
            cursor = self.get_tile(cursor.x - 1, cursor.y)
        if cursor is not position:
            result.add(Tile(cursor.x - 1, cursor.y))

        cursor = position
        # Right horizontally
        while self.get_tile(cursor.x + 1, cursor.y) is not None:
            cursor = self.get_tile(cursor.x + 1, cursor.y)
        if cursor is not position:
            result.add(Tile(cursor.x + 1, cursor.y))

        return result

    def _get_valid_queen_moves(self, position, subset):
        result = set()

        for tile in _make_tiles_around(position):
            if self.get_tile(tile.x, tile.y) is None \
                    and self.check_physically_allowed(position, tile):
                result.add(tile)

        return result.intersection(subset)

    @staticmethod
    def _get_valid_beetle_moves(original_tile, subset):
        result = set()

        for tile in _make_tiles_around(original_tile):
            result.add(tile)

        return result.intersection(subset)

    def _get_valid_mosquito_moves(self, original_tile, subset):
        result = set()

        for tile in self.get_tiles_around(original_tile):
            if tile.type == "ant":
                result = result.union(self._get_valid_ant_moves(original_tile, subset))
            elif tile.type == "grasshopper":
                result = result.union(self._get_valid_grasshopper_moves(original_tile))
            elif tile.type == "queen":
                result = result.union(self._get_valid_queen_moves(original_tile, subset=subset))
            elif tile.type == "beetle":
                result = result.union(self._get_valid_beetle_moves(original_tile, subset=subset))
            elif tile.type == "spider":
                result = result.union(self._get_valid_spider_moves(original_tile, subset=subset))
            elif tile.type == "ladybug":
                result = result.union(self._get_valid_ladybug_moves(original_tile, subset=subset))

        return result

    def _get_valid_spider_moves(self, original_tile, subset):
        checks = [original_tile]

        prev_area = set()
        area = set()
        for i in range(3):
            prev_area = area
            area = set()

            # Create area of tiles
            for check in checks:
                for tile in _make_tiles_around(check):
                    if tile not in subset:
                        continue
                    if self.get_tile(tile.x, tile.y) is None \
                            and self.check_physically_allowed(check, tile):
                        area.add(tile)

            checks = [a for a in area]

        result = area - prev_area

        return result

    def _get_valid_ladybug_moves(self, original_tile, subset):
        result = set()

        area = set()
        checks = [original_tile]
        for i in range(2):
            area = set()
            # Create area of tiles
            for check in checks:
                for tile in self.get_tiles_around(check):
                    area.add(tile)

            checks = [a for a in area]

        for piece in area:
            for tile in _make_tiles_around(piece):
                if self.get_tile(tile.x, tile.y) is None:
                    result.add(tile)

        return result.intersection(subset)

    def _get_valid_ant_moves(self, original_tile, subset):
        """
        Ants may only move to unoccupied spaces.

        :param position:
        :param subset:
        :return:
        """
        frontier = [original_tile]

        result = set()
        while True:
            area = set()
            # Create area of tiles
            for check in frontier:
                for tile in _make_tiles_around(check):
                    if tile not in subset:
                        continue
                    if self.get_tile(tile.x, tile.y) is None \
                            and self.check_physically_allowed(check, tile):
                        area.add(tile)

            frontier = area.copy()

            temp_result = result.union(area)
            if temp_result == result:
                return temp_result

            result = temp_result


    def fix_height(self, tiles: set):
        for tile in tiles:
            board_tile = self.get_tile(tile.x, tile.y)
            if board_tile is not None:
                tile.z = board_tile.z + 1

    def get_tile(self, x: int, y: int) -> Optional[Tile]:
        try:
            temp = self.tiles[y][x]
            return temp[len(temp) - 1]
        except (IndexError, KeyError) as e:
            return None

    def put_tile(self, tile):
        if tile.y not in self.tiles:
            self.tiles[tile.y] = {}
        if tile.x not in self.tiles[tile.y]:
            self.tiles[tile.y][tile.x] = []

        tile.z = len(self.tiles[tile.y][tile.x])
        self.tiles[tile.y][tile.x].append(tile)

    def move(self, player: Player, data):
        x = int(data.get("new_x"))
        y = int(data.get("new_y"))
        original_x = data.get("x", None)
        original_y = data.get("y", None)

        tile = Tile(x, y)
        tile.owner = player.user.name
        tile.type = data.get("image")

        original_tile = None
        if original_x is not None:
            original_x = int(original_x)
            original_y = int(original_y)
            original_tile = self.get_tile(original_x, original_y)

            # Placing the tile back on the original position is valid, and will not use up a turn.
            if original_tile.x == tile.x and original_tile.y == tile.y:
                return True

        # Check if the user has enough tiles left to place this one.
        if original_tile is None and not player.can_move(tile.type):
            return False

        # Check if the queen restriction has been met by turn 4
        if player.queen_restriction(tile.type):
            return False

        if self.is_move_valid(original_tile, tile, player):
            # Remove tile on previous location
            if original_tile is not None:
                self.remove_tile(original_tile.x, original_tile.y)

            self.put_tile(tile)

            # If this is a new tile, subtract the tile from the amounts
            if original_tile is None:
                player.pieces[tile.type] -= 1

            player.turn += 1
            self.next_turn()
            return True

        return False

    def export_valid_moves(self, x, y, user):
        # This get can only fail if the user makes an invalid request.
        original_tile = self.get_tile(x, y)

        moves = self.get_valid_moves(original_tile, user)
        self.fix_height(moves)
        return moves

    def get_tiles_around(self, tile):
        tiles = []

        surroundings = _make_tiles_around(tile)
        for around in surroundings:
            hive_tile = self.get_tile(around.x, around.y)
            if hive_tile is not None:
                tiles.append(hive_tile)

        return tiles

    def breaks_hive(self, move):
        """
        Checks if, after removing this tile, the hive is still a singular unit.
        It may not be separated into two parts.

        :param move:
        :return:
        """

        excluded = self.tiles[move.y][move.x].pop()

        hive_tiles = set()
        for y, row in self.tiles.items():
            for x, _ in row.items():
                tile = self.get_tile(x, y)
                if tile is not None:
                    hive_tiles.add(tile)

        # Do a breadth first search starting from a random tile.
        # If the resulting set contains all tiles, it is valid
        starting_point = self._get_random_tile()

        bfs_tiles = set()
        frontier = [starting_point]

        while len(frontier) != 0 and starting_point is not None:
            selection = frontier.pop()
            bfs_tiles.add(selection)
            for tile in self.get_tiles_around(selection):
                # Only add tiles to frontier if it has not yet been added to the list.
                if tile not in bfs_tiles:
                    frontier.append(tile)

        self.put_tile(excluded)

        return bfs_tiles != hive_tiles

    def remove_tile(self, x, y):
        self.tiles[y][x].pop()
        if len(self.tiles[y][x]) == 0:
            del self.tiles[y][x]

    def get_player(self, name) -> Optional[Player]:
        for player in self.players:
            if player.user.name == name:
                return player

        return None

    def get_player_list(self):
        players = [{
            "name": player.user.name,
            "elo": player.user.elo,
            "type": "player",
            "turn": self.get_turn() == player
        } for player in self.players]

        spectators = [{
            "name": player.user.name,
            "elo": player.user.elo,
            "type": "spectator",
            "turn": False
        } for player in self.spectators]

        return players + spectators

    def remove_player(self, username):
        player = self.get_player(username)
        if player is not None:
            self.players.remove(player)
        else:
            self.spectators.remove(username)

    def finished(self):
        for y, row in self.tiles.items():
            for x, tiles in row.items():
                for tile in tiles:
                    if tile.type == "queen" and len(self.get_tiles_around(tile)) == 6:
                        self.loser = tile.owner

                        for player in self.players:
                            if player.user.name != self.loser:
                                self.winner = player.user.name

                        return True

        return False

    def check_physically_allowed(self, position: Tile, tile: Tile):
        direction = get_direction(position, tile)
        if direction is None:
            raise ValueError("Cannot check when tiles are more than 1 space apart.")

        tr = self._get_top_right(position) is None
        left = self.get_tile(position.x - 1, position.y) is None
        if direction == Directions.TOP_LEFT:
            return tr or left

        br = self._get_bottom_right(position) is None
        if direction == Directions.BOTTOM_LEFT:
            return br or left
        if direction == Directions.RIGHT:
            return tr or br

        tl = self._get_top_left(position) is None
        bl = self._get_bottom_left(position) is None
        if direction == Directions.LEFT:
            return tl or bl

        right = self.get_tile(position.x + 1, position.y) is None
        if direction == Directions.TOP_RIGHT:
            return tl or right
        if direction == Directions.BOTTOM_RIGHT:
            return bl or right

    def reset_game(self):
        self.tiles = {}

        self.turn = 0
        self.turn_number = 0
        self.winner = None
        self.loser = None

        for player in self.players:
            player.reset()
