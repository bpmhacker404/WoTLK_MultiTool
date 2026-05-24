import dataclasses

_fields = {
    'id': int,
    'name': str,
    'file_name': str,
    'area': float,
    'scale': float,
    'min_scale': float,
    'max_scale': float,
}

SpellVisualEffectNameRecord = dataclasses.make_dataclass('SpellVisualEffectNameRecord', zip(_fields.keys(), _fields.values()))
SpellVisualEffectNameRecord.field_types = staticmethod(_fields.values())
