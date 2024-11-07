from datetime import datetime
from utils.common import get_logger
from db_handling.user_handler import add_user, validate_user_creds
from flask import Flask, render_template, request, redirect, url_for, jsonify
from db_handling.data_handler import get_latest_program_id, get_workouts_dict_from_program_id

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
    # try:
    #     pass
    # except ValueError as e:
    #     status = 400
    #     resp = jsonify({'status': 'failed',
    #                     'error_msg': f'User name {username} and email {user_email} does not exist'})
    #     return

    return redirect(url_for(f'program_view', user_id=user_id))


@app.route('/sign_up', methods=['POST'])
def sign_up():
    user_email = request.form.get('email')
    username = request.form.get('username')
    user_password = request.form.get('password')
    user_password = '1234'
    user_id = add_user(username, user_email, user_password)
    # try:
    #     pass
    # except ValueError as e:
    #     status = 400
    #     resp = jsonify({'status': 'failed',
    #                     'error_msg': f'Unable to add user {username} with email {user_email} to user data base'})
    #     return

    return redirect(url_for('program_view'))


@app.route('/program_view/<user_id>')
def program_view(user_id: str):
    program_id = get_latest_program_id(user_id)
    workouts = get_workouts_dict_from_program_id(program_id)
    return render_template('program_view.html', workouts=workouts)
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
# @app.route('/submit_set', methods=['POST'])
# def set_as_highest_priority(**kwargs):
#     recording_id = request.form.get('recording_id')
#     global job_type_to_queue_map
#     priority_to_update = job_type_to_queue_map['mp4']['waiting'].make_recording_first(recording_id)
#     set_priority_for_recording(recording_id, priority_to_update)
#     return redirect(url_for('mp4_waiting_queue'))
#
#
# @app.route('/submit', methods=['POST'])
# def submit():
#     # Retrieve form data & Validate input
#     recording_info_dict = \
#         {'recording_path': request.form['recording_path'],
#          'type': request.form['recording_type'],
#          'car': request.form['car'],
#          'recording_source': request.form['recording_source'],
#          'is_delete': request.form.get('is_delete', True),
#          'dc_user_email': validate_user_email(request.form['email'], request.form.get('from_automation', False)),
#          'cam_params': validate_camera_params(request.form['camera_parameters']),
#          'notes': request.form['notes'],
#          'status': STATUS.QUEUED.name,
#          'jira_ticket': request.form.get('jira_ticket', None),
#          'ros_bag_path': request.form.get('ros_bag_path', None)}
#
#     recording_name_to_file_paths_map, recording_name_to_sdc_file = None, None
#
#     # Get the metadata fields
#     for metadata_field_name in METADATA_FIELD_NAMES:
#         recording_info_dict[metadata_field_name] = request.form.getlist(metadata_field_name)
#
#     if recording_info_dict['type'].lower() == 'mp4':
#         recording_name_to_file_paths_map, recording_name_to_sdc_file, recording_name_to_gps_files = get_dir_struct_from_mp4_dir_path(
#             recording_info_dict['recording_path'], recording_info_dict['recording_source'])
#
#     elif recording_info_dict['type'].lower() == 'magna':
#         recording_name_to_split_structs_map = get_dir_struct_from_magna_dir_path(recording_info_dict['recording_path'])
#     else:
#         # Todo: add support for pcap
#         pass
#
#     new_recording_ids = []
#     # Insert the recordings to the DB
#     creation_date = datetime.now().strftime(DATETIME_STR_FORMAT)
#     (rec_name_to_split_paths_map, rec_name_to_split_ids_map, rec_name_to_sdc_paths_map, rec_name_to_sdc_ids_map,
#      rec_name_to_rec_id_map) = None, None, None, None, None
#
#     if recording_info_dict['recording_source'] == 'gdrive':
#         maps = create_maps_from_gdrive_inputs(recording_name_to_file_paths_map, recording_name_to_sdc_file, recording_name_to_gps_files)
#         (rec_name_to_split_paths_map, rec_name_to_split_ids_map, rec_name_to_sdc_paths_map,
#          rec_name_to_sdc_ids_map, rec_name_to_rec_id_map, rec_name_to_gps_id_and_path_map) = maps
#
#     if recording_info_dict['type'].lower() == 'mp4':
#         new_recording_ids = _get_recording_ids_from_mp4_recording(recording_info_dict, recording_name_to_file_paths_map,
#                                                                   recording_name_to_sdc_file,
#                                                                   rec_name_to_split_paths_map,
#                                                                   rec_name_to_split_ids_map, rec_name_to_sdc_paths_map,
#                                                                   rec_name_to_sdc_ids_map, rec_name_to_rec_id_map,
#                                                                   creation_date)
#
#     elif recording_info_dict['type'].lower() == 'magna':
#         new_recording_ids = _get_recording_ids_from_magna_recording(recording_info_dict,
#                                                                     recording_name_to_split_structs_map, creation_date)
#     for recording_name, file_paths in recording_name_to_file_paths_map.items():
#         recording_info_dict['date_created'] = creation_date
#         recording_info_dict["first_recording_path"] = file_paths[0] if not recording_info_dict[
#                                                                                'recording_source'] == 'gdrive' else \
#             rec_name_to_split_paths_map[recording_name[1]][0]
#
#         single_recording_dict = {k: v for k, v in recording_info_dict.items()}
#
#         if recording_info_dict['recording_source'] != 'gdrive' and recording_name in recording_name_to_sdc_file:
#             single_recording_dict["sdc_file_path"] = recording_name_to_sdc_file[recording_name]
#         elif recording_info_dict['recording_source'] == 'gdrive' and recording_name[1] in rec_name_to_sdc_paths_map:
#             single_recording_dict["sdc_file_path"] = rec_name_to_sdc_paths_map[recording_name[1]]
#             single_recording_dict["sdc_file_gdrive_ids"] = rec_name_to_sdc_ids_map[recording_name[1]]
#
#         if recording_info_dict['recording_source'] == 'gdrive':
#             single_recording_dict["recording_gdrive_id"] = rec_name_to_rec_id_map[recording_name[1]]
#             file_paths = rec_name_to_split_paths_map[recording_name[1]]
#             file_path_to_file_gdrive_id_map = {file_paths[i]: rec_name_to_split_ids_map[recording_name[1]][i] for i in
#                                                range(len(file_paths))}
#         else:
#             file_path_to_file_gdrive_id_map = None
#
#         if recording_info_dict['recording_source'] == 'gdrive' and recording_name[1] in rec_name_to_gps_id_and_path_map:
#             single_recording_dict["gps_file_path_to_id"] = rec_name_to_gps_id_and_path_map[recording_name[1]]
#
#         recording_id, _ = insert_new_documents_from_recording(single_recording_dict, recording_name, file_paths,
#                                                               file_path_to_file_gdrive_id_map)
#         new_recording_ids.append(recording_id)
#
#     # queue new recordings
#     job_type = recording_info_dict['type'].lower()
#     new_recordings = get_recordings_by_id(new_recording_ids)
#     job_type_to_queue_map[job_type]['waiting'].enqueue_recordings(new_recordings)
#
#     # Redirect to the add_to_queue page after processing
#     return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
