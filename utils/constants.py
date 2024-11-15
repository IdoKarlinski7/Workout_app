from enum import IntEnum

DAY_NAME_FORMAT = "%A"
DATETIME_STR_FORMAT = "%Y_%m_%d_%H_%M_%S"

OBJECT_ID_FIELDS = ['_id', 'user_id', 'program_id', 'workout_id', 'exercise_id', 'linked_exercise_id']

class SetType(IntEnum):

    REGULAR = 0
    DOWN_SET = 1
    SUPER_SET = 2
    MYOREPS = 3
    MYOREPS_MATCH = 4

class DayNames(IntEnum):

    Sunday = 1
    Monday = 2
    Tuesday = 3
    Wednesday = 4
    Thursday = 5
    Friday = 6
    Saturday = 7
