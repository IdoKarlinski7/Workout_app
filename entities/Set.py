from datetime import datetime
from entities.db_object import DbObject


class Set(DbObject):

    UPDATABLE_FIELDS = ['rir', 'rep_count', 'date_performed']

    INSERT_MUST_HAVE_FIELDS = ['order', 'target', 'date_created', 'exercise_id', 'rep_count', 'rir']

    def __init__(self, exercise_id: str = None, order: int = None, target: int = None, rep_count: int = -1,
                 date_created: datetime = None, date_performed: str = None, rir: int = 2, _id = None):

        super().__init__(_id, date_created)
        self.rir = rir
        self.order = order
        self.target = target
        self.rep_count = rep_count
        self.exercise_id = exercise_id
        self.date_performed = date_performed

    def timed_clone(self, exclude_attrs: [str] = None):
        other = super().timed_clone(exclude_attrs)
        other.rep_count = -1
        other.date_performed = None
        other.exercise_id = None