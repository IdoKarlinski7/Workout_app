from entities.Set import Set
from datetime import datetime
from utils.constants import SetType
from entities.db_object import DbObject


class Exercise(DbObject):

    UPDATABLE_FIELDS = ['set_count', 'weight', 'last_edited']
    INIT_MUST_HAVE_FIELDS = ['name', 'set_type', 'workout_id', 'last_edited', 'weight', 'order', 'set_count',
                             'rest_period', 'min_reps', 'max_reps']

    def __init__(self, name: str = None, set_type: SetType = None, workout_id: str = None, last_edited: datetime = None,
                 weight: float = None, order: int = None, set_count: int = None, rest_period: float = None,
                 date_created: datetime = None, min_reps: int = None, max_reps: int = None, sets: [Set] = None, _id = None):

        updatable = Exercise.verify_init(locals())

        super().__init__(_id, date_created, last_edited, updatable)
        self.name = name
        self.sets = sets
        self.order = order
        self.weight = weight
        self.max_reps = max_reps
        self.min_reps = min_reps
        self.set_count = set_count
        self.workout_id = workout_id
        self.set_type = set_type.name
        self.rest_period = rest_period
        self.last_edited = last_edited
