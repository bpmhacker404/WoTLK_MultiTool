import dataclasses

_fields = {
    'id': int,
    'parent_spell_visualkit': int,
    'spell_visualeffect_name': int,
    'attachment_id': int,
    'offsetX': float,
    'offsetY': float,
    'offsetZ': float,
    'yaw': float,
    'pitch': float,
    'row': float,
}

SpellVisualKitModelAttachRecord = dataclasses.make_dataclass('SpellVisualKitModelAttachRecord', zip(_fields.keys(), _fields.values()))
SpellVisualKitModelAttachRecord.field_types = staticmethod(_fields.values())
