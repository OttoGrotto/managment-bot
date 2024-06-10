from .data import Routing

class OSRS:
    """
    Get user stats from the OSRS HiScores API

    Parameters:
        user: str
    """
    def __init__(self, user: str, type: str) -> None:
        self.user = user
        self.type = type
        self.routing = Routing(self.user, self.type)

    def get(self):
        return self.routing.get()