from datetime import datetime
from entities.Exercise import Exercise
from entities.db_object import DbObject

class Workout(DbObject):

    UPDATABLE_FIELDS = ['dates_performed']

    INIT_MUST_HAVE_FIELDS = ['name', 'program_id', 'order', 'date_created', 'scheduled_day']

    def __init__(self, name: str = None, program_id: str = None, order: int = None, scheduled_day: str = None,
                 date_created: datetime = None, dates_performed: [str] = None, _id = None, exercises: [Exercise] = None):

        updatable = Workout.verify_init(locals())

        super().__init__(_id, date_created, updatable)
        self.name = name
        self.order = order
        self.exercises = exercises
        self.program_id = program_id
        self.scheduled_day = scheduled_day
        self.dates_performed = dates_performed