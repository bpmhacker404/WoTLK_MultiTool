import dataclasses

_fields = {
    'id': int,
    'object_effect_package_id': int,
    'object_effect_group_id': int,
    'state_type': int,
}

ObjectEffectsPackageElemRecord = dataclasses.make_dataclass('ObjectEffectsPackageElemRecord', zip(_fields.keys(), _fields.values()))
ObjectEffectsPackageElemRecord.field_types = staticmethod(_fields.values())
