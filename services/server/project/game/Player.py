#
# Used to track all player related information.
# For example; if it is the player's turn, a reference to the game board, and the amount of pieces allowed to play.
#
from project.database import user_service
from project.database.models import UserModel


class Player:
    def __init__(self, board, user: UserModel):
        self.board = board
        self.user = user
        self.pieces = {
            "queen": 1,
            "spider": 2,
            "beetle": 2,
            "grasshopper": 3,
            "ant": 3,
            "mosquito": 1,
            "ladybug": 1
        }
        self.turn = 0

    def get_tile_amounts(self):
        result = []
        for key in self.pieces.keys():
            result.append({
                "name": key,
                "amount": self.pieces[key]
            })

        return result

    def can_move(self, piece):
        return self.pieces[piece] > 0

    def queen_restriction(self, piece):
        # In turn 4 the queen has to have been placed.
        if self.turn >= 3 and piece != "queen" and self.pieces["queen"] != 0:
            return True
        return False

    def reset(self):
        self.user = user_service.get_user(name=self.user.name)
        self.pieces = {
            "queen": 1,
            "spider": 2,
            "beetle": 2,
            "grasshopper": 3,
            "ant": 3,
            "mosquito": 1,
            "ladybug": 1
        }
        self.turn = 0
