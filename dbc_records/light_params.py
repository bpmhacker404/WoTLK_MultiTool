import dataclasses

_fields = {
    'id': int,
    'high_light_sky': int,
    'light_skybox_id': int,
    'cloud_type_id': int,
    'glow': float,
    'water_shallow_alpha': float,
    'water_deep_alpha': float,
    'ocean_shallow_alpha': float,
    'ocean_deep_alpha': float,
}

LightParamsRecord = dataclasses.make_dataclass('LightParamsRecord', zip(_fields.keys(), _fields.values()))
LightParamsRecord.field_types = staticmethod(_fields.values())
