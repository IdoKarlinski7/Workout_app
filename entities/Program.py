from datetime import datetime
from entities.Workout import Workout
from entities.db_object import DbObject

class Program(DbObject):

    UPDATABLE_FIELDS = []

    INIT_MUST_HAVE_FIELDS = ['user_id', 'date_created', 'name', 'total_workouts']

    def __init__(self, user_id: str = None, date_created: datetime = None, name: str = None,
                 total_workouts: int = None, workouts: [Workout] = None, _id = None):

        updatable = Program.verify_init(locals())

        super().__init__(_id, date_created, updatable)
        self.name = name
        self.user_id = user_id
        self.workouts = workouts
        self.total_workouts = total_workouts

