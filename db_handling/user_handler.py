import pymongo
from db_handling.db_client_handler import get_db_client
from utils.common import get_md5_from_string, get_logger


def add_user(username: str, user_email: str, password: str = '', db_client: pymongo.MongoClient = None) -> str:

    logger = get_logger()
    db_client = get_db_client(db_client)
    password_md5 = get_md5_from_string(password)
    user_info = {'username': username, 'email': user_email, 'password_hash': password_md5}

    logger.info(f'Inserting new user with info - \n {user_info}')

    resp = db_client.User_data.User.insert_one(user_info)
    if not resp.inserted_id:
        logger.error('Failed to insert document')
        raise ValueError('Failed to insert document')

    return str(resp.inserted_id)


def validate_user_creds(username: str, user_email: str, password: str = '', db_client: pymongo.MongoClient = None) -> str:

    logger = get_logger()
    db_client = get_db_client(db_client)
    user_info = {'username': username, 'email': user_email}
    logger.info(f'Finding user with info - \n {user_info}')

    doc = db_client.User_data.User.find_one(user_info)
    if not doc:
        raise ValueError(f'Unable To find user name {username} with email {user_email}')

    password_md5 = get_md5_from_string(password)
    if doc and doc['password_hash'] != password_md5:
        raise ValueError('Password provided did not match.')

    return str(doc['_id'])
