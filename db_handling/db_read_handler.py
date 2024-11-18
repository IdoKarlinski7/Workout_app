import pymongo
from bson import ObjectId
from pymongo.synchronous.client_session import ClientSession

from utils.common import get_logger
from entities.Program import Program
from entities.Workout import Workout
from entities.Exercise import Exercise
from db_handling.db_client_handler import get_db_client

LOGGER = get_logger()


def get_data(collection_name: str, db_client: pymongo.MongoClient, session: ClientSession = None,
             document_ids: [ObjectId] = None, query: dict = None, project: {str: int} = None) -> [dict]:

    project = project if project else {}

    if query is None and document_ids is None:
        LOGGER.error(f'Unable to get data without a query of a list of IDs.')
        raise ValueError

    LOGGER.info(f'Getting documents with projection {project} from collection {collection_name}')

    _query = query if query else {'_id': {"$in": document_ids}}

    result = list(db_client['Data'][collection_name].find(_query, project, session=session))

    return result


def get_exercise_list_from_ids(exercise_ids: [ObjectId], db_client: pymongo.MongoClient, session: ClientSession) -> [Exercise]:

    exercise_docs = get_data(collection_name='Exercise', document_ids=exercise_ids,
                             db_client=db_client, session=session)

    exercise_list = [Exercise(**doc) for doc in exercise_docs]

    if not _verify_single_workout_id_from_exercise_list(exercise_list):
        raise ValueError('Unable to get a single workout id from exercise list.')

    return exercise_list


def _verify_single_workout_id_from_exercise_list(exercise_list: [Exercise]) -> bool:
    workout_ids = list({obj.workout_id for obj in exercise_list})
    return len(workout_ids) == 1


def get_workout_from_exercise_ids(exercise_ids: [ObjectId], db_client: pymongo.MongoClient, session: ClientSession) -> dict:

    _pipeline = [
        {
            "$match": {
            "_id": {"$in": exercise_ids}
        }},
        {"$addFields": {
            "workout_obj_id": {"$toObjectId": "workout_id"}
        }},
        {
            "$lookup": {
            "from": "Workout",
            "localField": 'workout_obj_id',
            "foreignField": '_id',
            "as": "workout"
        }},
        {"$project": {
            "_id": 0,
            "workout": 1
        }}
    ]

    workouts = list(db_client.Data.Exercise.aggregate(_pipeline, session=session))

    workouts = list({doc['workout'] for doc in workouts})

    if len(workouts) > 1:
        LOGGER.error(f'Got more that one workout ids from list of exercise ids')
        raise ValueError

    return workouts[0]


def get_program_from_workout(workout: Workout, db_client: pymongo.MongoClient, session: ClientSession) -> Program:
    program_id = ObjectId(workout.program_id)
    [program_doc] = get_data('Program', db_client=db_client, session=session, document_ids=[program_id])
    return Program(**program_doc)


def get_program_workouts_from_workout_id(workout_id: ObjectId, db_client: pymongo.MongoClient, session: ClientSession) -> [Workout]:
    _pipeline = [
    {"$match":
         {"_id": workout_id}
    },
    {"$lookup": {
            "from": "Workout",
            "localField": "program_id",
            "foreignField": "program_id",
            "as": "all_workouts"}
    },
    {"$unwind":
            "all_workouts"
     },
    {"$replaceRoot":
            {"newRoot": "all_workouts"}
     },
    {"$project": {
            "order": 1,
            "completed": 1,
            "name": 1,
            "program_id": 1,
            "last_edited": 1,
            "date_created": 1

    }}
    ]
    return [Workout(**doc) for doc in list(db_client.Data.Workout.aggregate(_pipeline, session=session))]


def get_exercises_list_from_workout_ids(workout_ids: [str], db_client: pymongo.MongoClient) -> [Exercise]:
    _pipeline = [
        {
            "$match": {
            "workout_id": {"$in": workout_ids},
            "date_performed": {"$exists": False}
        }},
        {"$addFields": {
            "exercise_id_str": {"$toString": "$_id"}
        }},
        {"$lookup": {
            "from": "Workout",
            "localField": "exercise_id_str",
            "foreignField": "exercise_id",
            "as": "sets"
            }},
        {"$project": {
            "exercise_id_str": 0
        }},
        {"$sort": {
            "date_created": -1
        }}
    ]

    result = list(db_client.Data.Exercise.aggregate(_pipeline))

    current_exercises = get_current_exercises_from_exercise_list(result)

    return [Exercise(**doc) for doc in current_exercises]


def get_current_exercises_from_exercise_list(exercise_list: [dict]) -> [dict]:

    current_exercises = [exercise_list[0]]

    for ex in exercise_list:
        if ex['name'] == current_exercises[-1]['name']:
            pass
        else:
            current_exercises.append(ex)

    return current_exercises


def get_workout_id_to_name_map(db_client: pymongo.MongoClient, workout_ids: [str] = None,
                                program_id: str = None) -> dict:

    _query = {'_id': {"$in": [ObjectId(_id) for _id in workout_ids]}} if workout_ids else {'program_id': program_id}
    _project = {"_id": 1, "name": 1, "order": 1}

    workouts_res = get_data('Workout', db_client, query=_query, project=_project)

    return {str(w["_id"]): w['name'] for w in workouts_res}


def get_workouts_dict_from_list_of_ids(workout_ids: [str], db_client: pymongo.MongoClient) -> dict:
    db_client = get_db_client(db_client)

    id_to_name_map = get_workout_id_to_name_map(workout_ids=workout_ids, db_client=db_client)

    exercises_list = get_exercises_list_from_workout_ids(workout_ids=workout_ids, db_client=db_client)

    return create_workouts_dict(workout_id_to_name=id_to_name_map, exercises=exercises_list)
