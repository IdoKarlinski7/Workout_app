import inspect
from logging import Logger
from utils.constants import OBJECT_ID_FIELDS


class DbObject:

    def to_dict(self) -> dict:
        instance_dict = {}
        for _mem in inspect.getmembers(self):
            if not _mem[0].startswith('_') and not inspect.ismethod(_mem[1]):
                attr_value = str(_mem[1]) if _mem[0] in OBJECT_ID_FIELDS else _mem[1]
                instance_dict[_mem[0]] = attr_value
        return instance_dict

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