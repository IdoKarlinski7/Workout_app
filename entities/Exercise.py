from enum import IntEnum
from utils import common
from bson import ObjectId
from entities.db_object import DbObject


class Exercise(DbObject):

    def __init__(self, name: str, set_type: IntEnum, workout_id: str, last_edited: str, weight: float,
                 order: int, set_count: int, rest_period: float, min_reps: int, max_reps: int,
                 linked_exercise_id: ObjectId = None, _id: ObjectId = None):

        super().__init__()
        self._id = _id
        self.name = name
        self.order = order
        self.weight = weight
        self.max_reps = max_reps
        self.min_reps = min_reps
        self.set_count = set_count
        self.workout_id = workout_id
        self.set_type = set_type.name
        self.rest_period = rest_period
        self.linked_exercise_id = linked_exercise_id
        self.last_edited = common.string_to_datetime(last_edited)
