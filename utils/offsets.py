from enum import IntEnum


class M2Offsets(IntEnum):
    # Длина 4 байта
    mdMagic = 0
    globalFlags = 16
    nGlobalSequences = 20
    ofsGlobalSequences = 24
    nAnimations = 28
    ofsAnimations = 32
    nAnimationLookup = 36
    ofsAnimationLookup = 40
    nBones = 44
    ofsBones = 48
    nViews = 68
    nColors = 72
    ofsColors = 76
    pivotPoint = 76
    nTextures = 80
    ofsTextures = 84
    nTransparency = 88
    ofsTransparency = 92
    nTextureAnimations = 96
    ofsTextureAnimations = 100
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
    nParticleEmitters = 296
    ofsParticleEmitters = 300
    nTextureCombiner = 304
    ofsTextureCombiner = 308


class M2Lengths(IntEnum):
    material = 4
    pivotPoint = 12
    texture = 16
    transparency = 20
    color = 40
    textureAnimation = 60
    animation = 64
    bone = 88
    particle = 476


class SkinOffsets(IntEnum):
    pass
