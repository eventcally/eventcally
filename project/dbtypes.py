from sqlalchemy import Integer
from sqlalchemy.types import TypeDecorator


class IntegerEnum(TypeDecorator):
    impl = Integer
    cache_ok = True

    def __init__(self, enumtype, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._enumtype = enumtype

    def process_bind_param(self, value, dialect):
        return value

    def process_result_value(self, value, dialect):
        if value:
            return self._enumtype(value)
        return None
