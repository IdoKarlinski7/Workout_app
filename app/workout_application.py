from datetime import datetime
from db_handling import db_api
from utils.common import get_logger
from db_handling.user_handler import add_user, validate_user_creds
from flask import Flask, render_template, request, redirect, url_for, jsonify

app = Flask(__name__, template_folder='templates')
logger = get_logger()

@app.route('/')
def home():
    return render_template('home.html')


@app.route('/is_alive', methods=['GET'])
def is_alive():
    return 'alive', 200


@app.route('/login', methods=['POST'])
def login():
    user_email = request.form.get('email')
    username = request.form.get('username')
    user_password = request.form.get('password')
    user_id = validate_user_creds(username, user_email, user_password)

    return redirect(url_for(f'programs_view', user_id=user_id))


@app.route('/sign_up', methods=['POST'])
def sign_up():
    user_email = request.form.get('email')
    username = request.form.get('username')
    user_password = request.form.get('password')
    user_id = add_user(username, user_email, user_password)

    return redirect(url_for(f'programs_view', user_id=user_id))


@app.route('/programs_view/<user_id>')
def programs_view(user_id: str):
    programs = db_api.get_programs_from_user_id(user_id)
    return render_template('programs_view.html', programs=programs)



@app.route('/get_program/<program_id>', methods=['GET'])
def get_program(program_id: str):
    workouts = db_api.get_workouts_dict_from_program_id(program_id)
    return render_template('program.html', workouts=workouts)
#
# @app.route('/programs_history')
# def magna_waiting_queue():
#     global job_type_to_queue_map
#     waiting_recordings = job_type_to_queue_map['magna']['waiting'].recordings
#
#     # Get the keys from the first dictionary to use as table headers
#     keys = WAITING_QUEUE_VALUES
#     metadata_keys = METADATA_FIELD_NAMES
#     indexed_entries = generate_indexes(waiting_recordings)
#     return render_template('magna_waiting_queue.html', metadata_keys=metadata_keys, keys=keys, entries=indexed_entries)
#
#
# @app.route('/set_target_for_exercise', method=['POST'])
# def mp4_in_process_queue():
#     global job_type_to_queue_map
#     in_process_recordings = get_sorted_recordings_by_status(STATUS.IN_PROGRESS, 'mp4', 50)
#
#     # Get the keys from the first dictionary to use as table headers
#     keys = WAITING_QUEUE_VALUES
#     metadata_keys = METADATA_FIELD_NAMES
#     indexed_entries = generate_indexes(in_process_recordings)
#     return render_template('mp4_in_process_queue.html', metadata_keys=metadata_keys, keys=keys, entries=indexed_entries)
#
#
@app.route('/submit_workout', methods=['POST'])
def submit_workout():
    exercise_to_sets_map = request.json.get('formData')
    print(exercise_to_sets_map)
    if exercise_to_sets_map is None:
        msg, status = 'Unable to fetch data', 400
    else:
        msg, status = 'Data received', 200

    db_api.submit_workout(exercise_to_sets_map)

    return msg, status

if __name__ == '__main__':
    app.run(debug=True)
