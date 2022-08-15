from TinyORM.database.database import Database
from TinyORM.database.tinydbdatabase import TinyDBDataBase


def db_init(db_type: str, info: dict):
    if db_type == 'TinyDB':
        return TinyDBDataBase(**info)
