
import json

class JsonteTypeRegister(object):
    def __init__(self, reserved_initial_chars = '$@#%*', escape_char = '$'):
        if not isinstance(escape_char, basestring) or len(escape_char) != 1:
            raise ValueError('escape_char must be a single character')
        if escape_char not in reserved_initial_chars:
            raise ValueError('escape_char must be in the reserved_initial_chars')

        self.reserved_initial_chars = reserved_initial_chars
        self.escape_char = escape_char

        self._serialisers = list()  # list of tuples ( Class , function that converts the object to a dict )
        self._deserialisers = []  # list of tuples ( #name , function that returns the object )

    def add_serialiser(self, obj_cls, obj_to_jsontedict_func):
        """
        :param obj_cls: The class to serialise
        :param obj_to_jsontedict_func: A function that turns an instance of the given class into a jsonte dict

        NOTE: The order that classes are added is important, since the first serialiser found that the object
              is an instance of will be used.

              For example, a datetime.datetime instance is both a datetime.datetime, and a datetime.date, so for
              correct serialisation the serialiser for datetime.datetime must be added first.
        """
        self._serialisers.append((obj_cls, obj_to_jsontedict_func))
    def add_deserialiser(self, name, dict_to_obj_func):
        if not name:
            raise ValueError('name must be at least one char long')
        if name[0] not in self.reserved_initial_chars:
            raise ValueError('name must start with a reserved char')
        if len(name) >= 2 and name[1] in self.reserved_initial_chars:
            raise ValueError('the 2nd char of the name must not be a reserved char')
        self._deserialisers.append((name, dict_to_obj_func))
    def _jsonte_objecthook(self, dct):
        assert isinstance(dct, dict)
        for keyname, dict_to_obj_func in self._deserialisers:
            if keyname in dct:
                return dict_to_obj_func(dct)
        for key in dct:
            if key[0] == self.escape_char:
                dct[key[1:]] = dct.pop(key)
        return dct

class JsonteDict(dict):
    pass

class JsonteEncoder(json.JSONEncoder):
    def __init__(self, jsonte_type_register, skipkeys=False, ensure_ascii=True,
            check_circular=True, allow_nan=True, sort_keys=False,
            indent=None, separators=None, encoding='utf-8'):
        assert isinstance(jsonte_type_register, JsonteTypeRegister)
        self.jsonte_type_register = jsonte_type_register
        self.reserved_initial_chars = self.jsonte_type_register.reserved_initial_chars
        self.escape_char = self.jsonte_type_register.escape_char
        self.jsonte_serialisers = self.jsonte_type_register._serialisers

        json.JSONEncoder.__init__(self, skipkeys=skipkeys, ensure_ascii=ensure_ascii, check_circular=check_circular,
                                  allow_nan=allow_nan, sort_keys=sort_keys, indent=indent, separators=separators,
                                  encoding=encoding )
    def default(self, obj):
        for cls, obj_to_jsontedict_func in self.jsonte_serialisers:
            if isinstance(obj, cls):
                value = obj_to_jsontedict_func(obj)
                if not isinstance(value, JsonteDict):
                    raise TypeError('serialisers must return a JsonteDict')
                return value
        return json.JSONEncoder.default(self, obj)
    def iterencode(self, obj, _one_shot=False):
        if isinstance(obj, dict) and not isinstance(obj, JsonteDict):
            # prefix any keys starting with something in reserved_initial_chars with the escape char
            keys_to_escape = [ key for key in obj if isinstance(key, basestring) and
                                            key[0] in self.reserved_initial_chars ]
            if keys_to_escape:
                new_dct = obj.copy()
                for key in keys_to_escape:
                    new_dct['%s%s' % (self.escape_char, key)] = new_dct.pop(key)
                return json.JSONEncoder.iterencode(self, new_dct, _one_shot)
        return json.JSONEncoder.iterencode(self, obj, _one_shot)
