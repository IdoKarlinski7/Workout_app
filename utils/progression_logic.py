from entities.Set import Set
from entities.Exercise import Exercise

ADD_WEIGHT_THRESHOLDS = {20: 16, 15: 12, 12: 10, 10: 8, 8: 6}

WEIGHT_RAISE_UNIT = 2.5

LOW_WEIGHT_THRESHOLD = 0.1
HIGH_WEIGHT_THRESHOLD = 0.04

def generate_sets_progression(sets: [Set], min_reps: int, max_reps: int) -> [bool, [Set]]:

    next_sets = []
    add_weight = False
    set_next_to_min = False
    previous_count = min_reps

    for _set in sets:
        new_set = _set.timed_clone()

        # Preformed reps up to the minimum required
        if _set.rep_count <= min_reps or set_next_to_min:
            new_set.target = min_reps
            set_next_to_min = True

        # Able to have a set with more reps despite fatigue
        if _set.rep_count > previous_count:
            next_sets[-1].target = _set.rep_count

        # Performed more reps than the required threshold to increase weight
        add_weight = _set.rep_count >= ADD_WEIGHT_THRESHOLDS[max_reps]

        new_set.target = min(_set.rep_count + 1, max_reps)
        previous_count = _set.rep_count

        next_sets.append(new_set)

    return add_weight, next_sets


def get_increased_weight(current_weight: float) -> float:

    is_low_weight = WEIGHT_RAISE_UNIT / current_weight > LOW_WEIGHT_THRESHOLD
    is_high_weight = WEIGHT_RAISE_UNIT / current_weight < HIGH_WEIGHT_THRESHOLD

    if is_low_weight:
        new_weight = current_weight + WEIGHT_RAISE_UNIT / 2

    elif is_high_weight:
        new_weight = current_weight + HIGH_WEIGHT_THRESHOLD * 2

    else:
        new_weight = current_weight + HIGH_WEIGHT_THRESHOLD

    return new_weight


def generate_progression_for_exercise(exercise: Exercise) -> Exercise:

    exercise.sets.sort(lambda x: x.order)
    add_weight, new_sets = generate_sets_progression(exercise.sets, exercise.min_reps, exercise.max_reps)

    new_exercise = exercise.timed_clone(exclude_attrs=['sets'])
    new_exercise.sets = new_sets

    if add_weight:
        new_exercise.weight = get_increased_weight(exercise.weight)

    return new_exercise


def generate_progression_for_exercise_list(exercise_list: [Exercise]) -> [Exercise]:

    next_exercises_for_workout = []

    for ex in exercise_list:
        next_ex = generate_progression_for_exercise(ex)
        next_exercises_for_workout.append(next_ex)

    return next_exercises_for_workout

