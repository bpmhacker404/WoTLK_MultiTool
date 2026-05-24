import dataclasses

_fields = {
    'id': int,
    'name': str,
    'object_effect_group_id': int,
    'trigger_type': int,
    'event_type': int,
    'effect_rec_type': int,
    'effect_rec_id': int,
    'attachment': int,
    'offsetX': int,
    'offsetY': int,
    'offsetZ': int,
    'object_effect_modifier': int,
}

ObjectEffectRecord = dataclasses.make_dataclass('ObjectEffectRecord', zip(_fields.keys(), _fields.values()))
ObjectEffectRecord.field_types = staticmethod(_fields.values())
