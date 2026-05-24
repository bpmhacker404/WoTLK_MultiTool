import dataclasses

_fields = {
    'id': int,
    'sound1': int,
    'sound2': int,
    'sound3': int,
    'sound4': int,
}

NPCSoundsRecord = dataclasses.make_dataclass('NPCSoundsRecord', zip(_fields.keys(), _fields.values()))
NPCSoundsRecord.field_types = staticmethod(_fields.values())
