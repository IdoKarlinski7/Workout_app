import copy
import inspect
from typing import Union
from bson import ObjectId
from logging import Logger
from datetime import datetime

from utils.common import datetime_now
from utils.constants import OBJECT_ID_FIELDS


class DbObject:

    UPDATABLE_FIELDS = []
    INIT_MUST_HAVE_FIELDS = []

    def __init__(self, _id: Union[ObjectId, str], date_created: datetime, last_edited: datetime, updatable: bool):
        self.updatable = updatable
        self.last_edited = last_edited
        self.date_created = date_created
        self._id = (_id if isinstance(_id, ObjectId) else ObjectId(_id)) if _id else None

    def get_id(self) -> ObjectId:
        return self._id

    def to_dict(self, include_id: bool = True) -> dict:
        instance_dict = {}

        for _mem in inspect.getmembers(self):

            if _mem[0] == "_id" and include_id:
                instance_dict[_mem[0]] = str(_mem[1])

            if not _mem[0].startswith('_') and not inspect.ismethod(_mem[1]):
                attr_value = str(_mem[1]) if _mem[0] in OBJECT_ID_FIELDS else _mem[1]
                instance_dict[_mem[0]] = attr_value

        return instance_dict

    def __eq__(self, other) -> bool:
        self_dict = self.to_dict()
        other_dict = other.to_dict()
        return self_dict == other_dict

    def __str__(self) -> str:
        return str(self.to_dict())

    def print(self, logger: Logger = None):
        instance_dict = self.to_dict()
        for k, v in instance_dict.items():
            print_format = f'{k} :  {v}\n'
            if logger:
                logger.info(print_format)
            else:
                print(print_format)

    def update_dict(self) -> [ObjectId, dict]:
        if not self.updatable:
            raise ValueError('Object is not updatable')

        new_field_values = {k: v for k, v in self.to_dict().items() if k in self.UPDATABLE_FIELDS and v is not None}

        return self._id, new_field_values

    def timed_clone(self, exclude_attrs: [str] = None):
        other = copy.deepcopy(self)
        other._id = None
        other.date_created = datetime_now()
        other.last_edited = datetime_now()

        if exclude_attrs:
            for attr_name in exclude_attrs:
                setattr(other, attr_name, None)
        return other


    @classmethod
    def verify_init_values_for_update(cls, init_values: dict) -> bool:
        return init_values.get('_id', False) and any([init_values.get(field) is not None for field in cls.UPDATABLE_FIELDS])

    @classmethod
    def verify_init_values(cls, init_values: dict) -> bool:
        return all([init_values.get(field) is not None for field in cls.INIT_MUST_HAVE_FIELDS])

    @classmethod
    def verify_init(cls, init_values: dict) -> bool:
        updatable = False
        if not cls.verify_init_values_for_update(locals()):
            raise ValueError(f'Unable to init object for update without any {cls.UPDATABLE_FIELDS}')
        else:
            updatable = True

        if not cls.verify_init_values(locals()):
            raise ValueError(f'Unable to init object without all {cls.INIT_MUST_HAVE_FIELDS}')

        return updatable