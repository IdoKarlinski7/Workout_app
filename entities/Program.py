from datetime import datetime
from entities.db_object import DbObject

class Program(DbObject):

    UPDATABLE_FIELDS = ['last_edited']
    INIT_MUST_HAVE_FIELDS = ['user_id', 'date_created', 'name', 'last_edited', 'total_workouts']

    def __init__(self, user_id: str = None, date_created: datetime = None, name: str = None,
                 last_edited: datetime = None, total_workouts: int = None, workout_ids: [str] = None, _id = None):

        updatable = Program.verify_init(locals())

        super().__init__(_id, date_created, last_edited, updatable)
        self.name = name
        self.user_id = user_id
        self.workout_ids = workout_ids
        self.last_edited = last_edited
        self.date_created = date_created
        self.total_workouts = total_workouts

