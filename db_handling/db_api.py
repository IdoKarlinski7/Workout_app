import pymongo
from bson import ObjectId
from pymongo.errors import PyMongoError

from entities.Set import Set
from utils.constants import SetType
from entities.Program import Program
from entities.Workout import Workout
from entities.Exercise import Exercise
import db_handling.data_handler as data_utils
from utils.common import get_logger, datetime_now
from db_handling.db_client_handler import get_db_client

LOGGER = get_logger()

def create_program(program_name: str, workouts_per_week: int, user_id: str) -> str:
    db_client = get_db_client()
    return data_utils.create_program(user_id=user_id, name=program_name, total_workouts=workouts_per_week,
                                           db_client=db_client)


def get_programs_from_user_id(user_id: str) -> list:

    db_client = get_db_client()

    if not isinstance(user_id, str):
        raise ValueError('User ID must be a string!')

    _query = {"user_id": user_id}
    user_programs = list(db_client.Data.Program.find(_query, sort=[('last_edited', -1)]))

    if not user_programs:
        raise ValueError(f'Unable to find program for user id - {user_id}')

    return user_programs


def get_workouts_dict_from_program_id(program_id: str) -> dict:

    db_client = get_db_client()

    id_to_name_map = data_utils.get_workout_id_to_name_map(program_id=program_id, db_client=db_client)

    exercises_list = data_utils.get_exercises_list_from_workout_ids(workout_ids=list(id_to_name_map.keys()), db_client=db_client)

    return data_utils.create_workouts_dict(workout_id_to_name=id_to_name_map, exercises=exercises_list)


def submit_workout(exercise_id_to_sets_map: {str: dict}):

    db_client = get_db_client()

    exercise_id_to_sets = {ObjectId(_id) : [Set(**set_dict) for set_dict in sets] for _id, sets in exercise_id_to_sets_map.items()}

    with db_client.start_session() as session:
        try:
            with session.start_transaction():

                data_utils.submit_workout(exercise_id_to_sets, db_client, session)

        except (ValueError, PyMongoError) as e:
            LOGGER.error(f'Unable to submit workout due to {e}')
            return

