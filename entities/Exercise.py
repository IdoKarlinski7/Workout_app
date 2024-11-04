from utils import common

class Exercise:

    def __init__(self, _id: str, name: str, set_type: str, workout_id: str, last_updated: str, weight: int,
                 set_count: int, rest_period: int, min_reps: int, max_reps: int, linked_exercise_id: str = None):

        self._id = _id
        self.name = name
        self.weight = weight
        self.max_reps = max_reps
        self.min_reps = min_reps
        self.set_type = set_type
        self.set_count = set_count
        self.workout_id = workout_id
        self.rest_period = rest_period
        self.linked_exercise_id = linked_exercise_id
        self.last_updated = common.string_to_datetime(last_updated)
