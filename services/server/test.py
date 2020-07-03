from project.game.Board import Board, Tile, TileTypes


def main():
    board = Board()

    tile = Tile(0, 0)
    tile.type = TileTypes.GRASSHOPPER

    tiles = board.get_tiles_around(tile)

    print("Test1`23")


if __name__ == "__main__":
    main()
