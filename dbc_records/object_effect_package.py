import dataclasses

_fields = {
    'id': int,
    'name': str,
}

ObjectEffectPackageRecord = dataclasses.make_dataclass('ObjectEffectPackageRecord', zip(_fields.keys(), _fields.values()))
ObjectEffectPackageRecord.field_types = staticmethod(_fields.values())
