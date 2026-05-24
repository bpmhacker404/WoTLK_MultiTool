import dataclasses

_fields = {
    'id': int,
    'sound_entry': int,
    'inner_radius': int,
    'timeA': int,
    'timeB': int,
    'timeC': int,
    'timeD': int,
    'random_offset': int,
    'usage': int,
    't_interval_min': int,
    't_interval_max': int,
    'volume_slide_cat': int,
    'duck_to_sfx': float,
    'duck_to_music': float,
    'duck_to_ambience': float,
    'inner_radius_influence': int,
    'outer_radius_influence': int,
    'time_to_duck': int,
    'time_to_unduck': int,
    'inside_angle': int,
    'outside_angle': int,
    'outside_volume': float,
    'outer_radius': int,
    'name': str,
}

SoundEntriesAdvancedRecord = dataclasses.make_dataclass('SoundEntriesAdvancedRecord', zip(_fields.keys(), _fields.values()))
SoundEntriesAdvancedRecord.field_types = staticmethod(_fields.values())
