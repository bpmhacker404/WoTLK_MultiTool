import dataclasses

_fields = {
    'id': int,
    'continent_id': int,
    'X': float,
    'Y': float,
    'Z': float,
    'falloff_start': float,
    'falloff_end': float,
    'light_params_id1': int,
    'light_params_id2': int,
    'light_params_id3': int,
    'light_params_id4': int,
    'light_params_id5': int,
    'light_params_id6': int,
    'light_params_id7': int,
    'light_params_id8': int,
}

LightRecord = dataclasses.make_dataclass('LightRecord', zip(_fields.keys(), _fields.values()))
LightRecord.field_types = staticmethod(_fields.values())
