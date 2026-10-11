from enum import IntEnum


class M2Offset(IntEnum):
    # Длина 4 байта
    mdMagic = 0
    globalFlags = 16
    nGlobalSeq = 20
    ofsGlobalSeq = 24
    nAnim = 28
    ofsAnims = 32
    nAnimLookup = 36
    ofsAnimLookup = 40
    nBones = 44
    ofsBones = 48
    nViews = 68
    nColors = 72
    ofsColors = 76
    pivotPnt = 76
    nTexs = 80
    ofsTexs = 84
    nTransp = 88
    ofsTransp = 92
    nTexAnims = 96
    ofsTexAnims = 100
    nMaterials = 112
    ofsMaterials = 116
    nBoneLookupTable = 120
    ofsBoneLookupTable = 124
    nTexLookup = 128
    ofsTexLookup = 132
    nTransLookup = 144
    ofsTransLookup = 148
    nTexAnimLookup = 152
    ofsTexAnimLookup = 156
    nPrtclEmitters = 296
    ofsPrtclEmitters = 300
    nTexCombiner = 304
    ofsTexCombiner = 308


class M2Length(IntEnum):
    material = 4
    pivotPnt = 12  # pivot point
    texture = 16
    transp = 20  # transparency
    color = 40
    texAnim = 60  # texture animation
    anim = 64  # animation
    bone = 88
    prtcl = 476  # particle


class SkinOffset(IntEnum):
    pass
