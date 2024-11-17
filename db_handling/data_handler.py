import pymongo
from bson import ObjectId
from pymongo.synchronous.client_session import ClientSession

from entities.Set import Set
from utils.constants import SetType
from entities.Program import Program
from entities.Workout import Workout
from utils.constants import DayNames
from entities.Exercise import Exercise
from entities.db_object import DbObject
import utils.progression_logic as logic
from utils.common import get_logger, datetime_now
from db_handling.db_client_handler import get_db_client

LOGGER = get_logger()

def insert_data(db_objects: [DbObject], collection_name: str, db_client: pymongo.MongoClient) -> [ObjectId]:

    format_docs = [_obj.to_dict(include_id=False) for _obj in db_objects]
    db_client = get_db_client(db_client)

    result = db_client['Data'][collection_name].insert_many(format_docs)
    inserted_ids = result.inserted_ids

    if len(inserted_ids) != len(db_objects):
        LOGGER.error(f'Able to insert only {len(inserted_ids)}/ {len(db_objects)} documents.')
        raise ValueError(f'Able to insert only {len(inserted_ids)}/ {len(db_objects)} documents.')

    return inserted_ids


def update_data(collection_name: str, db_client: pymongo.MongoClient,
                session: ClientSession, db_objects: [DbObject] = None, update_many: bool = False, document_ids: [ObjectId] = None,
                update_dict: {str: str} = None) -> [ObjectId]:
    LOGGER.info(f'Updating ids for collection {collection_name}')

    db_client = get_db_client(db_client)

    if update_many:
        if document_ids and update_dict:
            result = db_client['Data'][collection_name].update_many({"_id": {"$in": document_ids}}, {"$set": update_dict})
        else:
            LOGGER.error(f'Unable to use update many operator without list of ids and an update dictionary')
    else:
        bulk_operations = []
        update_time = datetime_now()
        if db_objects is None:
            LOGGER.error(f'Unable to perform a bulk write operation without a list of Objects')
        else:
            for db_obj in db_objects:
                db_obj.last_edited = update_time
                obj_id, values_dict = db_obj.update_dict()
                update_op = pymongo.UpdateOne({"_id": obj_id}, {"$set": values_dict})
                bulk_operations.append(update_op)

            result = db_client['Data'][collection_name].bulk_write(bulk_operations, session=session)

    modified_count = result.modified_count

    if len(modified_count) != len(db_objects):
        LOGGER.warning(f'Able to update only {len(modified_count)}/ {len(db_objects)} documents.')

    return modified_count


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


def create_program(user_id: str, name: str, total_workouts: int, db_client: pymongo.MongoClient = None) -> str:

    db_client = get_db_client(db_client)

    _program = Program(user_id=user_id, name=name, total_workouts=total_workouts, date_created=datetime_now())

    [program_id] = insert_data([_program], 'Program', db_client)
    return str(program_id)


def create_workout(name: str, order: int, program_id: str, scheduled_day: str, db_client: pymongo.MongoClient = None) -> str:

    db_client = get_db_client(db_client)

    _workout = Workout(name=name, order=order, program_id=program_id,date_created=datetime_now(), scheduled_day=scheduled_day)

    [workout_id] = insert_data([_workout], 'Workout', db_client)
    return str(workout_id)


def create_exercise(workout_id: str, name: str, order: int, weight: float, max_reps: int, min_reps: int, set_count: int,
                    rest_period: float, set_type: SetType = SetType.REGULAR, db_client: pymongo.MongoClient = None) -> str:

    db_client = get_db_client(db_client)

    _exercise = Exercise(name=name, workout_id=workout_id, order=order, weight=weight, max_reps=max_reps,
                         min_reps=min_reps, set_type=set_type, set_count=set_count, rest_period=rest_period)

    [exercise_id] = insert_data([_exercise], 'Exercise', db_client)
    create_sets(set_count=set_count, exercise_id=exercise_id, target=min_reps)
    return str(exercise_id)


def create_sets(set_count: int, exercise_id: str, target: int, db_client: pymongo.MongoClient = None) -> [str]:

    db_client = get_db_client(db_client)

    sets = []
    for order in range(1, set_count + 1):
        sets.append(Set(order=order, exercise_id=exercise_id, target=target))
    set_ids = insert_data(sets, 'Set', db_client)

    return [str(_id) for _id in set_ids]


def add_sets_to_exercise(exercise: Exercise, amount_to_add: int, db_client: pymongo.MongoClient):

    sets_start_idx = exercise.set_count + 1
    sets_end_idx = sets_start_idx + amount_to_add
    sets = []

    for order in range(sets_start_idx, sets_end_idx):
        sets.append(Set(order=order, exercise_id=str(exercise.get_id()), target=exercise.min_reps))

    set_ids = insert_data(sets, 'Set', db_client)

    return [str(_id) for _id in set_ids]


def get_exercise_list_from_ids(exercise_ids: [ObjectId], db_client: pymongo.MongoClient, session: ClientSession) -> [Exercise]:

    _project = {'workout_id': 1, 'set_count': 1, 'weight': 1, '_id': 1}

    exercise_docs = get_data(collection_name='Exercise', project=_project, document_ids=exercise_ids,
                             db_client=db_client, session=session)

    exercise_list = [Exercise(**doc) for doc in exercise_docs]

    if not _verify_single_workout_id_from_exercise_list(exercise_list):
        raise ValueError('Unable to get a single workout id from exercise list.')

    return exercise_list


def _verify_single_workout_id_from_exercise_list(exercise_list: [Exercise]) -> bool:
    workout_ids = list({obj.workout_id for obj in exercise_list})
    return len(workout_ids) == 1


def submit_workout(exercise_id_to_sets: {ObjectId: Set}, db_client: pymongo.MongoClient, session: ClientSession):

    def _get_aligned_exercise_list():
        _exercise_list = get_exercise_list_from_ids(list(exercise_id_to_sets.keys()), db_client, session)
        for ex in _exercise_list:
            ex.sets = exercise_id_to_sets.get(ex.get_id(), [])
        return _exercise_list

    date_performed = datetime_now(as_string=True)

    LOGGER.info(f'Getting Exercise object list and aligning sets to exercise')
    exercise_list = _get_aligned_exercise_list()

    LOGGER.info(f'Updating Sets in DB')
    update_sets_info(exercise_id_to_sets, date_performed, db_client, session)

    LOGGER.info(f'Updating Exercises in DB')
    update_sets_info(exercise_id_to_sets, date_performed, db_client, session)

    LOGGER.info(f'Updating Workout in DB')
    update_workout_info(exercise_id_to_sets, date_performed, db_client, session)

    LOGGER.info(f'Generating new Data for next workout in DB')
    generate_next_workout(exercise_list, db_client)

    return


def update_sets_info(exercise_id_to_sets: {ObjectId: Set}, date_performed: str,
                       db_client: pymongo.MongoClient, session: ClientSession):

    LOGGER.info(f'Update sets performed in DB')

    sets_to_update = []
    for _set in exercise_id_to_sets.values():
        _set.date_performed = date_performed
        sets_to_update.append(_set)

    update_data(db_objects=sets_to_update, collection_name='Set', db_client=db_client, session=session)


def update_exercises_info(exercise_id_to_sets: {ObjectId: Set}, date_performed: str,
                       db_client: pymongo.MongoClient, session: ClientSession):

    LOGGER.info(f'Update exercises performed in DB')

    exercise_ids = [_id for _id in exercise_id_to_sets.keys()]

    date_update = {"date_performed": date_performed}

    update_data(collection_name='Exercise', db_client=db_client, session=session, update_many=True,
                document_ids=exercise_ids, update_dict=date_update)


def update_workout_info(exercise_id_to_sets: {ObjectId: Set}, date_performed: str,
                       db_client: pymongo.MongoClient, session: ClientSession):

    exercise_ids = [_id for _id in exercise_id_to_sets.keys()]

    workout_dict = get_workout_from_exercise_ids(exercise_ids, db_client, session)

    workout = Workout(**workout_dict)

    workout.dates_performed.append(date_performed)

    update_data(collection_name='Exercise', db_client=db_client, session=session, db_objects=[workout])


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


def generate_next_workout(exercise_list: [Exercise], db_client: pymongo.MongoClient):

    LOGGER.info(f'Generating new targets for next workout')
    next_exercises = logic.generate_progression_for_exercise_list(exercise_list)

    new_exercises = []
    sets_with_same_exercise_id = []

    for next_ex in next_exercises:
        # exercise itself was modified
        if not next_ex.get_id():
            new_exercises.append(next_ex)
        # only need to insert new sets
        else:
            sets_with_same_exercise_id += next_ex.sets

    if new_exercises:
        LOGGER.info(f'Insert new Exercises with updated weights')
        insert_data(new_exercises, 'Exercise', db_client)

    LOGGER.info(f'Insert new Sets with updated targets and empty rep count')
    insert_data(sets_with_same_exercise_id, 'Set', db_client)


def get_exercises_list_from_workout_ids(workout_ids: [str], db_client: pymongo.MongoClient) -> [Exercise]:
    _pipeline = [
        {
            "$match": {
            "workout_id": {"$in": workout_ids}
        }},
        {"$addFields": {
            "exercise_id_str": {"$toString": "$_id"}
        }},
        {
            "$lookup": {
            "from": "Set",
            "let": { "exercise_id": "$exercise_id_str", "result_limit": "$set_count" },
            "pipeline": [
                { "$match": {
                    "$expr": { "$eq": ["$exercise_id_str", "$$exercise_id"] }
                }},
                { "$sort": { "date_created": -1 } },
                { "$limit": "$$result_limit" }
        ],
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


def create_workouts_dict(workout_id_to_name: dict, exercises: [Exercise]) -> dict:

    workouts_dict = {v: [] for v in workout_id_to_name.values()}

    for _exercise in exercises:
        _name = workout_id_to_name[_exercise.workout_id]

        workouts_dict[_name].append(_exercise.to_dict())

    return workouts_dict


def get_workouts_dict_from_list_of_ids(workout_ids: [str], db_client: pymongo.MongoClient) -> dict:
    db_client = get_db_client(db_client)

    id_to_name_map = get_workout_id_to_name_map(workout_ids=workout_ids, db_client=db_client)

    exercises_list = get_exercises_list_from_workout_ids(workout_ids=workout_ids, db_client=db_client)

    return create_workouts_dict(workout_id_to_name=id_to_name_map, exercises=exercises_list)


# def make_aggregation_query(db_client: pymongo.MongoClient, collection_name: str, match: {str:str}, session: ClientSession = None,
#                            add_fields: {str: str} = None, lookup: {str: str} = None, unwind: {str: str} = None,
#                            replace_root: {str: str} = None, project: {str: str} = None, sort: {str: str} = None) -> [dict]:
#
#     aggregation_pipeline = [{"$match": match}]
#
#     if add_fields is not None:
#         aggregation_pipeline.append({"$addFields": add_fields})
#
#     if add_fields is not None:
#         aggregation_pipeline.append({"$addFields": add_fields})
#
#     if lookup is not None:
#         aggregation_pipeline.append({"$lookup": lookup})
#
#     if unwind is not None:
#         aggregation_pipeline.append({"$unwind": unwind})
#
#     if replace_root is not None:
#         aggregation_pipeline.append({"$replaceRoot": replace_root})
#
#     if add_fields is not None:
#         aggregation_pipeline.append({"$addFields": add_fields})
#
#     if project is not None:
#         aggregation_pipeline.append({"$project": project})
#
#     if sort is not None:
#         aggregation_pipeline.append({"$sort": sort})
#
#     return list(db_client['Data'][collection_name].aggregate(pipeline=aggregation_pipeline, session=session))




if __name__ == "__main__":
    mongo_client = get_db_client()
    prog_id = create_program('672b814418822137da5fae4b', 'AB', 4)

    workout_id_a1 = create_workout('A1', 1, prog_id, DayNames.Sunday.name)
    create_exercise(workout_id_a1, 'Weighted Pull Ups', 1, 5, 12, 8, 2, 2)
    create_exercise(workout_id_a1, 'Pull Ups', 2, 0, 12, 8, 2, 2)
    create_exercise(workout_id_a1, 'Flexion Rows', 3, 50, 20, 12, 3, 2)
    create_exercise(workout_id_a1, 'Incline Dumbbell Curls', 4, 10, 20, 12, 4, 2)
    create_exercise(workout_id_a1, 'Leg Press', 5, 135, 20, 12, 3, 2)
    create_exercise(workout_id_a1, 'Leg Curls', 6, 55, 20, 12, 3, 2)

    workout_id_b1 = create_workout('B1', 2, prog_id, DayNames.Monday.name)
    create_exercise(workout_id_b1, 'Incline Bench Press', 1, 62.5, 20, 12, 3, 2)
    create_exercise(workout_id_b1, 'Dips', 2, 0, 20, 12, 2, 2)
    create_exercise(workout_id_b1, 'Push Ups', 3, 0, 20, 12, 2, 2)
    create_exercise(workout_id_b1, 'Seated Lateral Raises', 4, 10, 20, 12, 3, 2)
    create_exercise(workout_id_b1, 'Liu Raises', 5, 5, 20, 12, 3, 2)
    create_exercise(workout_id_b1, 'Skull Crushers', 6, 35, 20, 12, 3, 2)

    workout_id_a2 = create_workout('A2', 3, prog_id, DayNames.Wednesday.name)
    create_exercise(workout_id_a2, 'Underhand Pull Ups', 1, 0, 20, 12, 3, 2)
    create_exercise(workout_id_a2, 'T-Bar Row', 2, 35, 20, 12, 3, 2)
    create_exercise(workout_id_a2, 'Incline Dumbbell Curls', 3, 10, 20, 12, 2, 2)
    create_exercise(workout_id_a2, 'RDL', 4, 60, 20, 12, 2, 2)
    create_exercise(workout_id_a2, 'Hack Squat', 5, 70, 20, 12, 3, 2)

    workout_id_b2 = create_workout('B2', 4, prog_id, DayNames.Thursday.name)
    create_exercise(workout_id_b2, 'Incline Dumbbell Flies', 1, 15, 20, 12, 3, 2)
    create_exercise(workout_id_b2, 'Incline Dumbbell Press', 2, 28, 20, 12, 3, 2)
    create_exercise(workout_id_b2, 'Seated Lateral Raises', 3, 10, 20, 12, 3, 2)
    create_exercise(workout_id_b2, 'Overhead Barbell Press', 4, 42.5, 20, 12, 2, 2)
    create_exercise(workout_id_b2, 'Overhead Triceps Extensions', 4, 22.5, 20, 12, 3, 2)


    pass