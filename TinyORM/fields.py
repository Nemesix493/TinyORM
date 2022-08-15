import json
import sys


class Field:
    def __init__(self, field_type, blank=False, default=None, serialize: bool = True):
        self.field_type = field_type
        self.blank = blank
        self.default = default
        self.serialize = serialize

    def save_function(self, value):
        return value

    def load_function(self, value):
        return value

    def check_field(self, value):
        return type(value) == self.field_type or (self.blank and value is None)


class StringField(Field):
    def __init__(self, blank=False, default=None):
        super(StringField, self).__init__(field_type=str, blank=blank, default=default)


class IntField(Field):
    def __init__(self, blank=False, default=None):
        super(IntField, self).__init__(field_type=int, blank=blank, default=default)


class FloatField(Field):
    def __init__(self, blank=False, default=None):
        super(FloatField, self).__init__(field_type=float, blank=blank, default=default)


class JsonField(Field):
    def __init__(self, blank=False, default=None, **kwargs):
        if 'field_type' in kwargs.keys():
            field_type = kwargs['field_type']
            self.custom_field_type = True
        else:
            field_type = str
            self.custom_field_type = False
        super(JsonField, self).__init__(field_type=field_type, blank=blank, default=default)

    def load_function(self, value):
        return json.loads(value)

    def save_function(self, value):
        return json.dumps(value)

    def check_field(self, value):
        if self.custom_field_type:
            return type(value) == self.field_type or (self.blank and value is None)
        return True


class RelationalField(Field):
    def init_relation(self, cls: type, name: str, **kwargs):
        pass


class DomesticKey(Field):
    def __init__(self, field_type, foreign_key_name):
        self.foreign_key_name = foreign_key_name
        super(DomesticKey, self).__init__(field_type=field_type, blank=True, default=None, serialize=False)

    def load_function(self, pk):
        query = {
            self.foreign_key_name: pk
        }
        return self.field_type.get_all(**query)

    def save_function(self, value):
        pass


class ForeignKey(RelationalField):
    def __init__(self, field_type, domestic_key_name: str = None, blank=False, default=None):
        super(ForeignKey, self).__init__(field_type=field_type, blank=blank, default=default)
        self.domestic_key_name = domestic_key_name

    def init_relation(self, cls: type, name: str, **kwargs):
        if not type(self.domestic_key_name) == str:
            self.domestic_key_name = f'{cls.__name__.lower()}s'
        setattr(self.field_type, self.domestic_key_name, DomesticKey(cls, foreign_key_name=name))

    def load_function(self, value):
        return self.field_type.get(pk=value)

    def save_function(self, value):
        if value.pk:
            return value.pk
        else:
            value.save()
            return value.pk


class OneToOneField(RelationalField):
    def __init__(self, field_type, related_name: str = None, blank=False, default=None):
        super(OneToOneField, self).__init__(field_type=field_type, blank=blank, default=default)
        self.relation_initialized = False
        self.related_name = related_name

    def init_relation(self, cls: type, name: str, **kwargs):
        if not type(self.related_name) == str:
            self.related_name = f'{cls.__name__.lower()}'
        rel = OneToOneField(cls, related_name=name)
        rel.relation_initialized = True
        setattr(self.field_type, self.related_name, rel)

    def load_function(self, value):
        return self.field_type.get(pk=value)

    def save_function(self, value):
        if value.pk:
            return value.pk
        else:
            value.save()
            return value.pk


class ManyToManyField(RelationalField):
    def __init__(self, field_type, module_name, related_name: str = None, blank=False, default=None):
        super(ManyToManyField, self).__init__(field_type=field_type, blank=blank, default=default, serialize=False)
        self.relation_initialized = False
        self.related_name = related_name
        self.relation_table = None
        self.module_name = module_name

    def init_relation(self, cls: type, name: str, **kwargs) -> None:
        """
        :param cls: type
        :param name: str
        :param model_class: ModelClass
        :return: None
        """
        if not self.relation_initialized:
            if 'model_class' in kwargs.keys():
                if isinstance(type(kwargs['model_class']), type) and kwargs['model_class'].__name__ == 'Model':
                    if not type(self.related_name) == str:
                        self.related_name = f'{cls.__name__.lower()}'
                    rel = ManyToManyField(field_type=cls, module_name=self.module_name, related_name=name)
                    relation_table_name = f'{name.capitalize()}s{self.related_name.capitalize()}s'
                    relation_table_props = {
                        f'{cls.__name__.lower()}': ForeignKey(
                            field_type=cls,
                            domestic_key_name=relation_table_name.lower()
                        ),
                        f'{self.field_type.__name__.lower()}': ForeignKey(
                            field_type=self.field_type,
                            domestic_key_name=relation_table_name.lower()
                        ),
                    }
                    self.relation_table = type(
                        relation_table_name,
                        tuple([kwargs['model_class']]),
                        relation_table_props
                    )
                    rel.relation_table = self.relation_table
                    setattr(sys.modules[self.module_name], self.relation_table.__name__, self.relation_table)
                    setattr(self.field_type, self.related_name, rel)
                    rel.relation_initialized = True
                    self.relation_initialized = True
                else:
                    raise TypeError('\'model_class\' wrong type must be a \'ModelClass\' !')
            else:
                raise Exception('No \'model_class\' argument given !')

    def load_function(self, pk):
        fk_name = getattr(self.field_type, self.related_name).field_type.__name__.lower()
        query = {
            fk_name: pk
        }
        relations = self.relation_table.get_all(**query)
        related_objects = []
        for relation in relations:
            related_objects.append(
                self.field_type.get(
                    pk=getattr(relation, self.field_type.__name__.lower())
                )
            )
        return ManyToManyList(field=self, iterable=related_objects)

    def save_function(self, value):
        pass


class ManyToManyList(list):
    def __init__(self, field: ManyToManyField, **kwargs):
        self.field = field
        super(ManyToManyList, self).__init__()
        if 'iterable' in kwargs.keys():
            for val in kwargs['iterable']:
                super(ManyToManyList, self).append(val)

    def append(self, item):
        if type(item) == self.field.field_type:
            super(ManyToManyList, self).append(item)
        else:
            raise ValueError(f'item is a {type(item)} but must be a {self.field.field_type} !')




