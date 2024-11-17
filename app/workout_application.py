from db_handling import db_api
from utils.common import get_logger
from utils.constants import SetType
from db_handling.user_handler import add_user, validate_user_creds
from flask import Flask, render_template, request, redirect, url_for, abort

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

    try:
        user_id = validate_user_creds(username, user_email, user_password)

    except Exception:
        abort(401)

    return redirect(url_for(f'programs_view', user_id=user_id))


@app.route('/sign_up', methods=['POST'])
def sign_up():

    user_email = request.form.get('email')
    username = request.form.get('username')
    user_password = request.form.get('password')

    try:
        user_id = add_user(username, user_email, user_password)
    except Exception:
        abort(401)

    return redirect(url_for(f'programs_view', user_id=user_id))


@app.route('/programs_view/<user_id>')
def programs_view(user_id: str):

    programs = db_api.get_programs_from_user_id(user_id)

    return render_template('programs_view.html', programs=programs, user_id=user_id)


@app.route('/create_program', methods=['POST'])
def create_program():
    user_id = request.form.get('user_id')
    return render_template('create_program.html', user_id=user_id)


@app.route('/create_workouts', methods=['POST'])
def create_workouts():

    user_id = request.form.get('user_id')
    program_name = request.form.get('program_name')
    workouts_amount = int(request.form.get('workouts_amount'))
    set_types = [_type.name for _type in SetType]

    try:
        program_id = db_api.create_program(program_name=program_name, workouts_per_week=workouts_amount, user_id=user_id)

    except Exception:
        abort(401)

    return render_template('create_workouts.html',set_types=set_types, program_id=program_id,
                           workouts_amount=workouts_amount, program_name=program_name)


@app.route('/add_exercises_to_workouts', methods=['POST'])
def add_exercises_to_workouts():
    program_id = request.form.get('program_id')
    workouts_amount = request.form.get('workouts_amount')

    return redirect(url_for(f'add_exercises.html', user_id=program_id, workouts_amount=workouts_amount))


@app.route('/get_program/<program_id>', methods=['GET'])
def get_program(program_id: str):
    workouts = db_api.get_workouts_dict_from_program_id(program_id)
    return render_template('program.html', workouts=workouts)


@app.route('/submit_workout', methods=['POST'])
def submit_workout():
    exercise_to_sets_map = request.json.get('formData')

    if exercise_to_sets_map is None:
        msg, status = 'Unable to fetch data', 400
    else:
        msg, status = 'Data received', 200

    db_api.submit_workout(exercise_to_sets_map)

    return msg, status

@app.errorhandler(401)
def unauthorized_error(error):
 return render_template('unauthorized.html'), 401

if __name__ == '__main__':
    app.run(debug=True)
