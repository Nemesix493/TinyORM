from TinyORM.database import Database
from tinydb import TinyDB
from tinydb.table import Document


class TinyDBDataBase(Database):
    def __init__(self, file):
        self.file = file
        self.db = TinyDB(file)

    def insert(self, cls, serialized_obj) -> int:
        table = self.db.table(name=cls.__name__.lower())
        return table.insert(serialized_obj)

    def update(self, cls, serialized_obj, pk):
        table = self.db.table(name=cls.__name__.lower())
        table.upsert(Document(serialized_obj, doc_id=pk))

    def get(self, cls, **request):
        table = self.db.table(name=cls.__name__.lower())
        if 'pk' in request.keys():
            result = table.get(doc_id=request['pk'])
            result['pk'] = request['pk']
            return result
