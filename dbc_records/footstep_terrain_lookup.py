import dataclasses

_fields = {
    'id': int,
    'creature_footstep_id': int,
    'terrain_sound_id': int,
    'sound_id': int,
    'sound_id_splash': int,
}

FootstepTerrainLookupRecord = dataclasses.make_dataclass('FootstepTerrainLookupRecord', zip(_fields.keys(), _fields.values()))
FootstepTerrainLookupRecord.field_types = staticmethod(_fields.values())
