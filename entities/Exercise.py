from entities.Set import Set
from datetime import datetime
from utils.constants import SetType
from entities.db_object import DbObject


class Exercise(DbObject):

    UPDATABLE_FIELDS = ['set_count', 'weight', 'min_reps', 'max_reps','set_type', 'rest_period', 'dates_performed']

    INSERT_MUST_HAVE_FIELDS = ['name', 'set_type', 'workout_id', 'weight', 'order', 'set_count',
                             'rest_period', 'min_reps', 'max_reps', 'date_created']

    def __init__(self, name: str = None, set_type: SetType = SetType.REGULAR, workout_id: str = None,
                 weight: float = None, order: int = None, set_count: int = None, rest_period: float = None,
                 date_created: datetime = None, min_reps: int = None, max_reps: int = None, date_performed: str = None,
                 sets: [Set] = None, _id = None):

        super().__init__(_id, date_created)
        self.name = name
        self.sets = sets
        self.order = order
        self.weight = weight
        self.max_reps = max_reps
        self.min_reps = min_reps
        self.set_count = set_count
        self.workout_id = workout_id
        self.set_type = set_type.name if isinstance(set_type, SetType) else set_type
        self.rest_period = rest_period
        self.date_performed = date_performed

    def timed_clone(self, exclude_attrs: [str] = None):
        other = super().timed_clone(exclude_attrs)
        other.date_performed = None