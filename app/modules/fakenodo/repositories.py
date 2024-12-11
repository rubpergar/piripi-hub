from app.modules.fakenodo.models import Zenodo
from core.repositories.BaseRepository import BaseRepository


class FakenodoRepository(BaseRepository):
    def __init__(self):
        super().__init__(Fakenodo)