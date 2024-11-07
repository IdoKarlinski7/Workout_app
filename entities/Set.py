from utils import common
from bson import ObjectId
from entities.db_object import DbObject

class Set(DbObject):

    def __init__(self, exercise_id: str, order: int, target: int, rep_count: int = -1, last_edited: str = None, rir: int = 2, _id: ObjectId = None):
        super().__init__()
        self._id = _id
        self.rir = rir
        self.order = order
        self.target = target
        self.rep_count = rep_count
        self.exercise_id = exercise_id
        self.last_edited = common.string_to_datetime(last_edited)
