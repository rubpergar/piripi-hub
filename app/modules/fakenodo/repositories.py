from app.modules.fakenodo.models import Fakenodo
from core.repositories.BaseRepository import BaseRepository


class FakenodoRepository(BaseRepository):
    def __init__(self):
        super().__init__(Fakenodo)

    def create_new_deposition(self, dep_metadata):
        return self.create(dep_metadata=dep_metadata)