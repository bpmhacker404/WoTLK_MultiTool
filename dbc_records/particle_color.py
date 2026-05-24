import dataclasses

_fields = {
    'id': int,
    'start_1': int,
    'start_2': int,
    'start_3': int,
    'mid_1': int,
    'mid_2': int,
    'mid_3': int,
    'end_1': int,
    'end_2': int,
    'end_3': int,
}

ParticleColorRecord = dataclasses.make_dataclass('ParticleColorRecord', zip(_fields.keys(), _fields.values()))
ParticleColorRecord.field_types = staticmethod(_fields.values())
