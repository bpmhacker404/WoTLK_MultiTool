import dataclasses

_fields = {
    'id': int,
    'name': str,
}

ObjectEffectGroupRecord = dataclasses.make_dataclass('ObjectEffectGroupRecord', zip(_fields.keys(), _fields.values()))
ObjectEffectGroupRecord.field_types = staticmethod(_fields.values())
