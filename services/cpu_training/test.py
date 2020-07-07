import random

import numpy as np

from project.database.models import UserModel
from project.game.Board import Board, Tile

MAX_MOVES = 50


TILE_TYPES = ["queen", "spider", "beetle", "grasshopper", "ant", "mosquito", "ladybug"]
NAMES = ["CPU1", "CPU2"]


def shift_to_00(tiles: dict):
    min_x = 9223372036854775806
    min_y = 9223372036854775806
    for y, row in tiles.items():
        if y < min_y:
            min_y = y
        for x, items in row.items():
            if x < min_x:
                min_x = x

    # TODO: Reorder to single dimension array
    data = np.zeros(26 * 26 * 14)
    for y, row in tiles.items():
        for x, items in row.items():
            top = items[-1]
            top_idx = TILE_TYPES.index(top.type)
            top_idx += 7 * top.owner == NAMES[0]

            coord = (y - min_y) * 26 + (x - min_x) + top_idx
            data[coord] = 1

    return data


def get_free_tiles(board: Board, name: str):
    frees = []
    for y, row in board.tiles.items():
        for x, col in row.items():
            for item in col:
                if item.owner != name:
                    continue
                if not board.breaks_hive(item):
                    frees.append(item)

    return frees


def select_move(board, player):
    x = y = None

    original_tiles = get_free_tiles(board, player.user.name)
    types = [k for k, v in player.pieces.items() if v > 0]

    if player.turn == 3 and "queen" in types:
        # Specific queen placement restriction
        move_type = "queen"

        valid_moves = board.get_hive_tiles()
        valid_moves = list(board.get_allied_squares(valid_moves, player))

        move = valid_moves[random.randrange(0, len(valid_moves))]
    else:
        add_new = random.randint(0, 1) == 0

        # 50/50 add new piece or move existing piece
        if len(types) > 0 and (add_new or len(original_tiles) == 0):
            move_type = types[random.randrange(0, len(types))]

            if board.turn_number == 0:
                move = Tile(0, 0)
            elif board.turn_number == 1:
                starting_point = board._get_random_tile()  # noqa
                move = Tile(starting_point.x - 1, starting_point.y)
            else:
                valid_moves = board.get_hive_tiles()
                valid_moves = list(board.get_allied_squares(valid_moves, player))

                move = valid_moves[random.randrange(0, len(valid_moves))]
        else:
            done = False
            original_tile = None
            valid_moves = []
            while not done:
                idx = random.randrange(0, len(original_tiles))
                original_tile = original_tiles.pop(idx)
                valid_moves = list(board.get_valid_moves(original_tile, player.user.name))
                if len(valid_moves) > 0:
                    break

            move_type = original_tile.type

            move = valid_moves[random.randrange(0, len(valid_moves))]
            x = original_tile.x
            y = original_tile.y

    return {
        "x": x,
        "y": y,
        "new_x": move.x,
        "new_y": move.y,
        "image": move_type
    }


def play(board, names: list):
    used_board_states = []

    for i in range(MAX_MOVES):
        if i % 10 == 0:
            print("Step:", i)
        name = names[i % 2]
        player = board.get_player(name)

        selected_move = select_move(board, player)
        board.move(player, selected_move)

        normalized_board = shift_to_00(board.tiles)
        used_board_states.append(normalized_board)

        if board.finished():
            print(board.winner, board.loser)
            # train(used_board_states, positive=(board.winner == names[0]))
            return


def main():
    board = Board()

    for name in NAMES:
        board.add_player(UserModel(name, ""))

    play(board, NAMES)


if __name__ == "__main__":
    main()
