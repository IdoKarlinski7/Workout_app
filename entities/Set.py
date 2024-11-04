from utils import common

class Set:

    def __init__(self, _id: str, exercise_id: str, rep_count: int, date_preformed: str, order: int, rir: int = 2):

        self._id = _id
        self.rir = rir
        self.order = order
        self.rep_count = rep_count
        self.exercise_id = exercise_id
        self.date_preformed = common.string_to_datetime(date_preformed)
