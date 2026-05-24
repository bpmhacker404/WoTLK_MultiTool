import dataclasses

_fields = {
    'id': int,
    'precast': int,
    'cast': int,
    'impact': int,
    'state': int,
    'state_done': int,
    'channel': int,
    'has_missile': int,
    'missile_model': int,
    'missile_path_type': int,
    'missile_dest': int,
    'missile_sound': int,
    'anim_event_sound': int,
    'flags': int,
    'caster_impact': int,
    'target_impact': int,
    'missile_attach': int,
    'missile_height': int,
    'missile_speed': int,
    'missile_approach': int,
    'missile_flags': int,
    'missile_motion': int,
    'missile_targeting': int,
    'instant_area': int,
    'impact_area': int,
    'persistent_area': int,
    'missile_cast_offsetX': float,
    'missile_cast_offsetY': float,
    'missile_cast_offsetZ': float,
    'missile_impact_offsetX': float,
    'missile_impact_offsetY': float,
    'missile_impact_offsetZ': float,
}

SpellVisualRecord = dataclasses.make_dataclass('SpellVisualRecord', zip(_fields.keys(), _fields.values()))
SpellVisualRecord.field_types = staticmethod(_fields.values())
