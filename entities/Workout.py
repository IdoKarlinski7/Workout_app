from utils import common

class Workout:

    def __init__(self, _id: str, name: str, program_id: str, order: int,
                 date_created: str, exercise_ids: [str], completed: bool):

        self._id = _id
        self.name = name
        self.order = order
        self.completed = completed
        self.program_id = program_id
        self.exercise_ids = exercise_ids
        self.date_created = common.string_to_datetime(date_created)
