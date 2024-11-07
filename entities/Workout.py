from utils import common
from bson import ObjectId
from entities.db_object import DbObject

class Workout(DbObject):

    def __init__(self, name: str, program_id: str, order: int, last_edited: str,
                 date_created: str, exercise_ids: [str], completed: bool, _id: ObjectId = None):
        super().__init__()
        self._id = _id
        self.name = name
        self.order = order
        self.completed = completed
        self.program_id = program_id
        self.exercise_ids = exercise_ids
        self.last_edited = common.string_to_datetime(last_edited)
        self.date_created = common.string_to_datetime(date_created)
