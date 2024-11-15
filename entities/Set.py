from datetime import datetime
from entities.db_object import DbObject


class Set(DbObject):

    UPDATABLE_FIELDS = ['rir', 'target', 'rep_count']
    INIT_MUST_HAVE_FIELDS = ['exercise_id', 'order', 'target', 'last_edited']

    def __init__(self, exercise_id: str = None, order: int = None, target: int = None, rep_count: int = -1,
                 date_created: datetime = None, rir: int = 2, _id = None):

        updatable = Set.verify_init(locals())

        super().__init__(_id, date_created, updatable)
        self.rir = rir
        self.order = order
        self.target = target
        self.rep_count = rep_count
        self.exercise_id = exercise_id

    def timed_clone(self, exclude_attrs: [str] = None):
        other = super().timed_clone()
        other.rep_count = -1