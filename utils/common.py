import os
import logging
from hashlib import md5
#from disutils import util
from datetime import datetime
from utils.constants import DATETIME_STR_FORMAT


def get_md5_from_string(string_to_hash: str) -> str:
    if not isinstance(string_to_hash, str):
        raise ValueError(f'Cannot hash a non string object!!!!!')
    md5_hash = md5(string_to_hash.encode())
    return md5_hash.hexdigest()


def generate_indexes(entries):
    return enumerate(entries, start=1)

def create_folder_output_file(file_path: str):
    if file_path is not None:
        dir_path = os.path.dirname(os.path.abspath(file_path))
        if dir_path != '':
            os.makedirs(dir_path, exist_ok=True)


def get_logger(log_path: str = None, handlers: list = None, level=logging.INFO, logger_name: str = None) -> logging.Logger:

    def set_logger_level(level: int, logger=None):
        logger = logger if logger else LOGGER
        logger.setLevel(level)

    global LOGGER

    if logger_name is not None:
        name = logger_name
    elif log_path is not None:
        name = os.path.basename(log_path)
    else:
        name = None

    LOGGER = logging.getLogger(name)

    for handler in logging.root.handlers[:]:
        if isinstance(handler, logging.FileHandler):
            logging.root.removeHandler(handler)
    log_format = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
    handlers = handlers if handlers is not None else []
    if log_path is not None:
        create_folder_output_file(log_path)
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(log_format)
        if file_handler not in handlers:
            handlers.append(file_handler)

    stdout_handler = logging.StreamHandler()
    stdout_handler.setFormatter(log_format)
    handlers.append(stdout_handler)
    logging.basicConfig(level=level, handlers=handlers, datefmt='%Y-%m-%d %H:%M:%S')
    for handler in handlers[:-1]:
        LOGGER.addHandler(handler)

    set_logger_level(level, LOGGER)

    return LOGGER


# def string_to_bool(input_str: str) -> bool:
#     if not isinstance(input_str, bool):
#         input_str = bool(util.strtobool(input_str))
#     return input_str


def string_to_datetime(date_str: str) -> datetime:
    if any([not s.isdigit() for s in date_str.split('_')]):
        raise ValueError('Got a non digits date.')
    return datetime.strptime(date_str, DATETIME_STR_FORMAT)


def datetime_to_string(datetime_date:datetime) -> str:
    if not isinstance(datetime_date, datetime):
        raise ValueError('Can not convert non datetime to string.')
    return datetime_date.strftime(DATETIME_STR_FORMAT)

def datetime_now() -> str:
    now = datetime.now()
    now = datetime.now()
    return now.strftime(DATETIME_STR_FORMAT)