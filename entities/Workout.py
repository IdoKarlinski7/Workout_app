from datetime import datetime
from entities.db_object import DbObject

class Workout(DbObject):

    UPDATABLE_FIELDS = ['last_edited', 'completed']
    INIT_MUST_HAVE_FIELDS = ['name', 'program_id', 'order', 'last_edited', 'date_created', 'scheduled_day']

    def __init__(self, name: str = None, program_id: str = None, order: int = None, last_edited: datetime = None,
                 scheduled_day: str = None, date_created: datetime = None, exercise_ids: [str] = None, _id = None):

        updatable = Workout.verify_init(locals())

        super().__init__(_id, date_created, last_edited, updatable)
        self.name = name
        self.order = order
        self.program_id = program_id
        self.last_edited = last_edited
        self.exercise_ids = exercise_ids
        self.date_created = date_created
        self.scheduled_day = scheduled_day
