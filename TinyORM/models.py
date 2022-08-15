from TinyORM import Field, RelationalField, ManyToManyField


class Model:
    database = None

    @classmethod
    def get(cls, **query):
        """

        :param query:
        :return:Model
        """
        doc = cls.database.get(cls=cls, **query)
        for key, val in cls.__dict__.items():
            if isinstance(val, Field):
                if not val.serialize:
                    doc[key] = val.load_function(doc['pk'])
        return cls(**doc)

    @classmethod
    def get_all(cls, **query):
        pass

    def __init__(self, **kwargs):
        if 'pk' in kwargs.keys():
            self.pk = kwargs['pk']
        else:
            self.pk = None
        for key, field in self.__class__.__dict__.items():
            if isinstance(field, Field) and key in kwargs.keys():
                self.__setattr__(key, field.load_function(kwargs[key]))
            elif isinstance(field, Field):
                self.__setattr__(key, field.default)

    def serialize(self):
        serialized_self = {}
        if self.check_all_attr():
            for key, field in self.__class__.__dict__.items():
                if isinstance(field, Field):
                    if field.serialize:
                        serialized_self[key] = field.save_function(self.__getattribute__(key))
        return serialized_self

    def save(self):
        if self.check_all_attr():
            for key, field in self.__class__.__dict__.items():
                if isinstance(field, Field):
                    if not field.serialize:
                        field.save_function(self.__getattribute__(item=key))
        if self.pk:
            self.database.update(self.__class__, self.serialize(), pk=self.pk)
        else:
            self.pk = self.database.insert(self.__class__, self.serialize())

    def check_all_attr(self) -> bool:
        for key, field in self.__class__.__dict__.items():
            if isinstance(field, Field):
                field.check_field(value=self.__getattribute__(item=key))
        return True

    def __getattribute__(self, item):
        self_class = super(Model, self).__getattribute__('__class__')
        if item in self_class.__dict__.keys():
            if issubclass(self_class.__dict__[item], Field):
                field = self_class.__dict__[item]
                if not field.serialize and type(field) != ManyToManyField and self.pk is not None:
                    self.__setattr__(item, field.load_function(pk=self.pk))
        return super(Model, self).__getattribute__(item)


class ModelClass(type):
    def __init__(cls, *args, **kwargs):
        super(ModelClass, cls).__init__(*args, **kwargs)
        many_to_many = []
        for key, field in cls.__dict__.items():
            if isinstance(field, RelationalField):
                if isinstance(field, ManyToManyField):
                    many_to_many.append({
                        'field': field,
                        'key': key,
                    })
                else:
                    field.init_relation(cls, key, model_class=Model)
        for many_field in many_to_many:
            many_field['field'].init_relation(cls, many_field['key'], model_class=Model)



Model = ModelClass(Model.__name__, (), dict(Model.__dict__))
