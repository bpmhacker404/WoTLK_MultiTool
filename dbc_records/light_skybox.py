import dataclasses

_fields = {
    'id': int,
    'name': str,
    'flags': int,
}

LightSkyBoxRecord = dataclasses.make_dataclass('LightSkyBoxRecord', zip(_fields.keys(), _fields.values()))
LightSkyBoxRecord.field_types = staticmethod(_fields.values())
