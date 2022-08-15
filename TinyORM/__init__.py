from TinyORM.fields import Field, FloatField, IntField, StringField, JsonField, ForeignKey, RelationalField, ManyToManyField, ManyToManyList
from TinyORM.database import Database, db_init
from TinyORM.models import Model, ModelClass
import inspect
import sys


def setup_database(db_type: str, info: dict):
    Model.database = db_init(db_type=db_type, info=info)

def print_models_instances(module_name):
    for name, obj in inspect.getmembers(sys.modules[module_name]):
        if isinstance(obj, ModelClass):
            if obj != Model:
                print(f'{name} :')
                for key, field in obj.__dict__.items():
                    if isinstance(field, Field):
                        print(f'    {key} -> {type(field)}, field_type -> {field.field_type}')



try:
    from settings import DB_SETTINGS
    setup_database(**DB_SETTINGS)
except ModuleNotFoundError or ImportError as e:
    DB_SETTINGS = {
        'db_type': 'TinyDB',
        'info': {'file': 'database.json'}
    }
    setup_database(**DB_SETTINGS)
