from . import Base
from .serializer import Serializer
import requests as req

class Routing(Base):
    def __init__(self, user, type) -> None:
        super().__init__(type)
        self.user = user

    def get(self) -> dict[str, tuple[int, int, int | None]]:
        res = req.get(self.HI_Scores_URL.format(self.user))
        if res.status_code != 404:
            serializer = Serializer(res.text.split("\n"))
            return serializer.format()
        else:
            raise ValueError("User not found")
