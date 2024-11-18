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
    INSERT_MUST_HAVE_FIELDS = []

    def __init__(self, _id: Union[ObjectId, str], date_created: datetime):
        self.date_created = date_created
        self._id = (_id if isinstance(_id, ObjectId) else ObjectId(_id)) if _id else None

    def get_id(self) -> ObjectId:
        return self._id

    def to_dict(self, include_id: bool = True) -> dict:
        instance_dict = {}

        if not self.verify_values_for_insert():
            raise ValueError(f'Object contains None values in values that should be inserted')

        for _mem in inspect.getmembers(self):

            if _mem[0] == "_id" and include_id:
                instance_dict[_mem[0]] = str(_mem[1])

            if not _mem[0].startswith('_') and not inspect.ismethod(_mem[1]):
                attr_value = str(_mem[1]) if _mem[0] in OBJECT_ID_FIELDS else _mem[1]
                instance_dict[_mem[0]] = attr_value

        return {k: v for k, v in instance_dict.items() if k in self.INSERT_MUST_HAVE_FIELDS}

    def update_dict(self) -> [ObjectId, dict]:
        if not self.verify_values_for_update():
            raise ValueError('Object is not updatable')

        return self._id, {k: v for k, v in self.to_dict().items() if k in self.UPDATABLE_FIELDS and v is not None}


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

    def timed_clone(self, exclude_attrs: [str] = None):
        other = copy.deepcopy(self)
        other._id = None
        other.date_created = datetime_now()

        if exclude_attrs:
            for attr_name in exclude_attrs:
                setattr(other, attr_name, None)

        return other

    def verify_values_for_update(self) -> bool:
        return any([getattr(self, field) is not None for field in self.UPDATABLE_FIELDS])

    def verify_values_for_insert(self) -> bool:
        return all([getattr(self, field) is not None for field in self.INSERT_MUST_HAVE_FIELDS])


    # @classmethod
    # def verify_init_values_for_update(cls, init_values: dict) -> bool:
    #     return init_values.get('_id', False) and any([init_values.get(field) is not None for field in cls.UPDATABLE_FIELDS])
    #
    # @classmethod
    # def verify_init_values_for_insert(cls, init_values: dict) -> bool:
    #     return all([init_values.get(field) is not None for field in cls.INSERT_MUST_HAVE_FIELDS])
    #
    # @classmethod
    # def verify_init(cls, init_values: dict) -> bool:
    #
    #     updatable = False
    #
    #     if not cls.verify_init_values_for_update(init_values):
    #         if cls.UPDATABLE_FIELDS:
    #             raise ValueError(f'Unable to init object for update without any {cls.UPDATABLE_FIELDS}')
    #     else:
    #         updatable = True
    #
    #     if not cls.verify_init_values_for_insert(init_values) and not updatable:
    #         raise ValueError(f'Unable to insert object without all {cls.INSERT_MUST_HAVE_FIELDS}')
    #
    #     return updatable