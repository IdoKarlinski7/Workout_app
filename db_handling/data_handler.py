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
import db_handling.db_read_handler as db_read
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
                obj_id, values_dict = db_obj.update_dict()
                update_op = pymongo.UpdateOne({"_id": obj_id}, {"$set": values_dict})
                bulk_operations.append(update_op)

            result = db_client['Data'][collection_name].bulk_write(bulk_operations, session=session)

    modified_count = result.modified_count

    if len(modified_count) != len(db_objects):
        LOGGER.warning(f'Able to update only {len(modified_count)}/ {len(db_objects)} documents.')

    return modified_count


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
                         date_created=datetime_now(), min_reps=min_reps, set_type=set_type, set_count=set_count,
                         rest_period=rest_period)

    [exercise_id] = insert_data([_exercise], 'Exercise', db_client)
    create_sets(set_count=set_count, exercise_id=exercise_id, target=min_reps)
    return str(exercise_id)


def create_sets(set_count: int, exercise_id: str, target: int, db_client: pymongo.MongoClient = None) -> [str]:

    db_client = get_db_client(db_client)

    sets = []
    for order in range(1, set_count + 1):
        sets.append(Set(order=order, exercise_id=exercise_id, target=target, date_created=datetime_now()))
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


def submit_workout(exercise_id_to_sets: {ObjectId: Set}, db_client: pymongo.MongoClient, session: ClientSession):

    def _get_aligned_exercise_list():
        _exercise_list = db_read.get_exercise_list_from_ids(list(exercise_id_to_sets.keys()), db_client, session)
        for ex in _exercise_list:
            ex.sets = exercise_id_to_sets.get(ex.get_id(), [])
        return _exercise_list

    date_performed = datetime_now(as_string=True)

    LOGGER.info(f'Getting Exercise object list and aligning sets to exercise')
    exercise_list = _get_aligned_exercise_list()

    LOGGER.info(f'Updating Sets in DB')
    update_sets_info(exercise_id_to_sets, date_performed, db_client, session)

    LOGGER.info(f'Updating Exercises in DB')
    update_exercises_info(exercise_id_to_sets, date_performed, db_client, session)

    LOGGER.info(f'Updating Workout in DB')
    update_workout_info(exercise_list, date_performed, db_client, session)

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


def update_workout_info(exercise_list: [Exercise], date_performed: str,
                       db_client: pymongo.MongoClient, session: ClientSession):
    workout_id = ObjectId(exercise_list[0].workout_id)
    workout_dict = db_read.get_data('Workout', db_client, document_ids=[workout_id])

    workout = Workout(**workout_dict[0])

    workout.dates_performed.append(date_performed)

    update_data(collection_name='Exercise', db_client=db_client, session=session, db_objects=[workout])


def generate_next_workout(exercise_list: [Exercise], db_client: pymongo.MongoClient):

    LOGGER.info(f'Generating new targets for next workout')
    next_exercises = logic.generate_progression_for_exercise_list(exercise_list)

    next_exercise_ids = insert_data(next_exercises, 'Exercise', db_client)

    exercise_name_to_id = db_read.get_data('Exercise', db_client, document_ids=[next_exercise_ids], project={'name': 1})
    exercise_name_to_id = {doc['name']: str(doc['_id']) for doc in exercise_name_to_id}

    next_sets = []
    for ex in exercise_list:
        for _set in ex.sets:
            _set.exercise_id = exercise_name_to_id[ex.name]
        next_sets += ex.sets

    next_set_ids = insert_data(next_sets, 'Set', db_client)


def create_workouts_dict(workout_id_to_name: dict, exercises: [Exercise]) -> dict:

    workouts_dict = {v: [] for v in workout_id_to_name.values()}

    for _exercise in exercises:
        _name = workout_id_to_name[_exercise.workout_id]

        workouts_dict[_name].append(_exercise.to_dict())

    return workouts_dict


if __name__ == "__main__":
    mongo_client = get_db_client()
    prog_id = create_program('672b814418822137da5fae4b', 'ExampleProgram', 4)

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