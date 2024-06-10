# Version: 0.1.0

__all__ = [
    "osrs", 
    "serializer"
    ]

__slots__ = [
    "osrs", 
    "serializer"
    ]

__version__ = "0.1.0"

__author__ = "Otto Grotto"

class Base:
    def __init__(self, type: str = None) -> None:
        if not type:
            raise ValueError("Account type is required")
        match type:
            case "normal":
                self.HI_Scores_URL = "https://secure.runescape.com/m=hiscore_oldschool/index_lite.ws?player={}"
            case "ironman":
                self.HI_Scores_URL = "https://secure.runescape.com/m=hiscore_oldschool_ironman/index_lite.ws?player={}"
            case "hardcore":
                self.HI_Scores_URL = "https://secure.runescape.com/m=hiscore_oldschool_hardcore_ironman/index_lite.ws?player={}"
            case "ultimate":
                self.HI_Scores_URL = "https://secure.runescape.com/m=hiscore_oldschool_ultimate/index_lite.ws?player={}"
            case "deadman":
                self.HI_Scores_URL = "https://secure.runescape.com/m=hiscore_oldschool_deadman/index_lite.ws?player={}"
            case "seasonal":
                self.HI_Scores_URL = "https://secure.runescape.com/m=hiscore_oldschool_seasonal/index_lite.ws?player={}"
            case "tournament":
                self.HI_Scores_URL = "https://secure.runescape.com/m=hiscore_oldschool_tournament/index_lite.ws?player={}"
            case _:
                raise ValueError("Unknown account type, please use one of the following: normal, ironman, hardcore, ultimate, deadman, seasonal, tournament")