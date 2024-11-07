from utils import common
from bson import ObjectId
from entities.db_object import DbObject

class Program(DbObject):

    def __init__(self, user_id: str, date_created: str, name: str,
                 last_edited: str, total_workouts: int, workout_ids: [str] = None, _id: ObjectId = None):
        super().__init__()
        self._id = _id
        self.name = name
        self.user_id = user_id
        self.workout_ids = workout_ids
        self.total_workouts = total_workouts
        self.last_edited = common.string_to_datetime(last_edited)
        self.date_created = common.string_to_datetime(date_created)

