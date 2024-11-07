import pymongo
from enum import IntEnum
from bson import ObjectId
from entities.Set import Set
from utils.constants import SetType
from collections import defaultdict
from entities.Program import Program
from entities.Workout import Workout
from entities.Exercise import Exercise
from entities.db_object import DbObject
from utils.common import get_logger, datetime_now
from db_handling.db_client_handler import get_db_client

LOGGER = get_logger()

def get_latest_program_from_user_id(user_id: str, db_client: pymongo.MongoClient = None) -> dict:
    db_client = get_db_client(db_client)
    if not isinstance(user_id, str):
        raise ValueError('User ID must be a string!')
    _query = {"user_id": user_id}
    latest_program = db_client.Data.Program.find_one(_query, sort=[('last_edited', -1)])
    if not latest_program:
        raise ValueError(f'Unable to find program for user id - {user_id}')
    return latest_program


def get_latest_program_id(user_id: str, db_client: pymongo.MongoClient = None) -> str:
    latest_program = get_latest_program_from_user_id(user_id, db_client)
    return str(latest_program['_id'])


def create_program(user_id: str, name: str, total_workouts: int) -> str:
    _program = Program(user_id=user_id, name=name, total_workouts=total_workouts,
                          date_created=datetime_now(), last_edited=datetime_now())
    [program_id] = _insert_data_docs([_program], 'Program')
    return str(program_id)


def create_workout(name: str, order: int, program_id: str, completed: bool = False, exercise_ids: list = None) -> str:
    _workout = Workout(name=name, order=order, program_id=program_id, completed=completed,
                       exercise_ids=exercise_ids, date_created=datetime_now(), last_edited=datetime_now())
    [workout_id] = _insert_data_docs([_workout], 'Workout')
    return str(workout_id)


def create_exercise(workout_id: str, name: str, order: int, weight: float, max_reps: int, min_reps: int, set_count: int,
                    rest_period: float, set_type: IntEnum = SetType.REGULAR, linked_exercise_id: ObjectId = None) -> str:

    _exercise = Exercise(name=name, workout_id=workout_id, order=order, weight=weight, max_reps=max_reps,
                         min_reps=min_reps, set_type=set_type, set_count=set_count, rest_period=rest_period,
                         linked_exercise_id=linked_exercise_id, last_edited=datetime_now())
    [exercise_id] = _insert_data_docs([_exercise], 'Exercise')
    set_ids = create_sets(set_count=set_count, exercise_id=exercise_id, target=min_reps)
    return str(exercise_id)

def create_sets(set_count: int, exercise_id: str, target: int) -> [str]:
    sets = []
    for order in range(1, set_count + 1):
        sets.append(Set(order=order, exercise_id=exercise_id, last_edited=datetime_now(), target=target))
    set_ids = _insert_data_docs(sets, 'Set')
    return [str(_id) for _id in set_ids]


def _insert_data_docs(doc_objects: [DbObject], collection_name: str, db_client: pymongo.MongoClient = None) -> [ObjectId]:
    format_docs = [_obj.to_dict() for _obj in doc_objects]
    db_client = get_db_client(db_client)
    result = db_client['Data'][collection_name].insert_many(format_docs)
    inserted_ids = result.inserted_ids
    if len(inserted_ids) != len(doc_objects):
        LOGGER.error(f'Able to insert only {len(inserted_ids)}/ {len(doc_objects)} documents.')
        raise ValueError(f'Able to insert only {len(inserted_ids)}/ {len(doc_objects)} documents.')
    return inserted_ids


def _update_data_docs(object_ids: [ObjectId], collection_name: str, update_field: {str: str}, db_client: pymongo.MongoClient = None) -> bool:
    if any([not isinstance(_id, ObjectId) for _id in object_ids]):
        raise ValueError('Received a non Bson object id')
    LOGGER.info(f'Updating ids for collection {collection_name} with field {update_field}')

    db_client = get_db_client(db_client)
    result = db_client['Data'][collection_name].update_many({"_id": {"$in": object_ids}}, update_field)
    updated_count = result.modified_count

    if updated_count != len(object_ids):
        LOGGER.warning(f'Able to insert only {updated_count}/ {len(object_ids)} documents.')

    return updated_count == len(object_ids)


def _get_exercises_list_from_workout_ids(workout_ids: [str], db_client: pymongo.MongoClient = None) -> list:
    db_client = get_db_client(db_client)
    _pipeline = [
    {"$match": {
            "workout_id": { "$in": workout_ids }}
    },
        {"$addFields": {
            "exercise_id": { "$toString": "$_id" }}
    },
    {"$lookup": {
            "from": "Set",
            "localField": "exercise_id",
            "foreignField": "exercise_id",
            "as": "sets"}
    },
    {"$project": {
            "_id": 0,
            "exercise_id": 0,
            "last_edited": 0,
            "sets.exercise_id": 0,
            "sets.last_edited": 0
        }
    }]
    return list(db_client.Data.Exercise.aggregate(_pipeline))


def _get_workout_id_to_name_map(workout_ids: [str] = None, program_id: str = None,
                                db_client: pymongo.MongoClient = None) -> dict:
    _query = {'_id': {"$in": [ObjectId(_id) for _id in workout_ids]}} if workout_ids else {'program_id': program_id}
    _project = {"_id": 1, "name": 1, "order": 1}
    workouts_res = list(db_client.Data.Workout.find(_query, _project))
    return {str(w["_id"]): w['name'] for w in workouts_res}

def _create_workouts_dict(workout_id_to_name: dict, exercises: [dict]) -> dict:
    workouts_dict = {v: [] for v in workout_id_to_name.values()}
    for _exercise in exercises:
        _name = workout_id_to_name[_exercise['workout_id']]
        del _exercise['workout_id']
        workouts_dict[_name].append(_exercise)

    return workouts_dict

def get_workouts_dict_from_list_of_ids(workout_ids: [str], db_client: pymongo.MongoClient = None) -> dict:
    db_client = get_db_client(db_client)

    id_to_name_map = _get_workout_id_to_name_map(workout_ids=workout_ids, db_client=db_client)

    exercises_list = _get_exercises_list_from_workout_ids(workout_ids=workout_ids, db_client=db_client)

    return _create_workouts_dict(workout_id_to_name=id_to_name_map, exercises=exercises_list)

def get_workouts_dict_from_program_id(program_id: str, db_client: pymongo.MongoClient = None) -> dict:
    db_client = get_db_client(db_client)

    id_to_name_map = _get_workout_id_to_name_map(program_id=program_id, db_client=db_client)

    exercises_list = _get_exercises_list_from_workout_ids(workout_ids=list(id_to_name_map.keys()), db_client=db_client)

    return _create_workouts_dict(workout_id_to_name=id_to_name_map, exercises=exercises_list)

if __name__ == "__main__":
    # program_id = create_program('672b814418822137da5fae4b', 'AB', 4)
    #
    # workout_id_a1 = create_workout('A1', 1, program_id)
    # create_exercise(workout_id_a1, 'Weighted Pull Ups', 1, 5, 12, 8, 2, 2.0)
    # create_exercise(workout_id_a1, 'Pull Ups', 2, 0, 12, 8, 2, 2.0)
    # create_exercise(workout_id_a1, 'Flexion Rows', 3, 50, 20, 12, 3, 2.0)
    # create_exercise(workout_id_a1, 'Incline Dumbbell Curls', 4, 10, 20, 12, 4, 2.0)
    # create_exercise(workout_id_a1, 'Leg Press', 5, 135, 20, 12, 3, 2.0)
    # create_exercise(workout_id_a1, 'Leg Curls', 6, 55, 20, 12, 3, 2.0)
    #
    # workout_id_b1 = create_workout('B1', 2, program_id)
    # create_exercise(workout_id_b1, 'Incline Bench Press', 1, 62.5, 20, 12, 3, 2.0)
    # create_exercise(workout_id_b1, 'Dips', 2, 0, 20, 12, 2, 2.0)
    # create_exercise(workout_id_b1, 'Push Ups', 3, 0, 20, 12, 2, 2.0)
    # create_exercise(workout_id_b1, 'Seated Lateral Raises', 4, 10, 20, 12, 3, 2.0)
    # create_exercise(workout_id_b1, 'Liu Raises', 5, 5, 20, 12, 3, 2.0)
    # create_exercise(workout_id_b1, 'Skull Crushers', 6, 35, 20, 12, 3, 2.0)
    #
    # workout_id_a2 = create_workout('A2', 3, program_id)
    # create_exercise(workout_id_a2, 'Underhand Pull Ups', 1, 0, 20, 12, 3, 2.0)
    # create_exercise(workout_id_a2, 'T-Bar Row', 2, 35, 20, 12, 3, 2.0)
    # create_exercise(workout_id_a2, 'Incline Dumbbell Curls', 3, 10, 20, 12, 2, 2.0)
    # create_exercise(workout_id_a2, 'RDL', 4, 60, 20, 12, 2, 2.0)
    # create_exercise(workout_id_a2, 'Hack Squat', 5, 70, 20, 12, 3, 2.0)
    #
    # workout_id_b2 = create_workout('B2', 4, program_id)
    # create_exercise(workout_id_b2, 'Incline Dumbbell Flies', 1, 15, 20, 12, 3, 2.0)
    # create_exercise(workout_id_b2, 'Incline Dumbbell Press', 2, 28, 20, 12, 3, 2.0)
    # create_exercise(workout_id_b2, 'Seated Lateral Raises', 3, 10, 20, 12, 3, 2.0)
    # create_exercise(workout_id_b2, 'Overhead Barbell Press', 4, 42.5, 20, 12, 2, 2.0)
    # create_exercise(workout_id_b2, 'Overhead Triceps Extensions', 4, 22.5, 20, 12, 3, 2.0)

    program_id = get_latest_program_id('672b814418822137da5fae4b')
    workouts = get_workouts_dict_from_program_id(program_id)
    pass