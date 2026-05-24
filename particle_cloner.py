from typing import BinaryIO

import dearpygui.dearpygui as dpg
import os
import pyperclip
import shutil

from utils.binary import Binary
from utils.offsets import M2Offsets, M2Lengths
from utils.registry import reg_manager
from utils.statusbar import StatusBar


class ParticlesCopyError(Exception):
    pass


class ParticleCloner:
    def __init__(self):
        self.m2From = None
        self.m2To = None
        self.nParticlesM2From = 0
        self.nParticlesM2To = 0
        self.particlesAddressM2From = 0
        self.particlesAdressM2To = 0
        self.nTexturesM2From = 0
        self.texturesAddressM2From = 0
        self.texturesNewAdressM2To = 0
        self.nBonesM2From = 0
        self.bonesAdressM2From = 0
        self.nBonesM2To = 0
        self.bonesAdressM2To = 0
        self.keyBoneIdsM2From = []
        self.keyBoneIdsM2To = {}
        self.isNeedToUpdateParticlePos = []
        self.existedTexturesIntM2To = None
        self.existedTexturesM2To = None
        self.saveExistingParticles = False
        self.identifyBones = True
        self.doNotCopyEnabledin = False
        # для enabledin
        self.nAnimationsM2From = 0
        self.animationsAdressM2From = 0
        self.nAnimationsM2To = 0
        self.nAnimationsM2To_bytes = None
        self.animationsAdressM2To = 0
        # Название полей из 010Editor
        self.idFlagsPos = []
        self.parentBone = []
        self.texture = []
        self.geometryModelLength = []
        self.geometryModelOffset = []
        self.recursionModelLength = []
        self.recursionModelOffset = []
        self.fromBlendingToTextureDimensionsColumns = []
        self.emissionSpeed = []
        self.emissionSpeedTimestampKeyFrame = []
        self.speedVar = []
        self.speedVarTimestampKeyFrame = []
        self.verticalRange = []
        self.verticalRangeTimestampKeyFrame = []
        self.horizontalRange = []
        self.horizontalRangeTimestampKeyFrame = []
        self.gravity = []
        self.gravityTimestampKeyFrame = []
        self.lifespan = []
        self.lifespanTimestampKeyFrame = []
        self.lifespanVary = []
        self.emissionRate = []
        self.emissionRateTimestampKeyFrame = []
        self.emissionRateVary = []
        self.emissionAreaLength = []
        self.emissionAreaLengthTimestampKeyFrame = []
        self.emissionAreaWidth = []
        self.emissionAreaWidthTimestampKeyFrame = []
        self.zSource = []
        self.zSourceTimestampKeyFrame = []
        self.colorTrackTimestampKeyFrame = []
        self.alphaTrackTimestampKeyFrame = []
        self.scaleTrackTimestampKeyFrame = []
        self.scaleVary = []
        self.headCellTrackTimestampKeyFrame = []
        self.tailCellTrackTimestampKeyFrame = []
        self.fromTailLengthToFollowScale2 = []
        self.nSplinePoints = []
        self.nSplinePointsOffset = []
        self.enabledinInterpolationGlobalId = []
        # Индексы/офсеты
        self.PARTICLE_INDEXES = (0, 20, 22, 24, 28, 32, 36, 40, 52, 56, 72, 76, 92, 96, 112, 116, 132, 136, 152, 156, 172, 176, 180, 196,
                                 200, 204, 220, 224, 240, 244, 260, 276, 292, 308, 316, 332, 348, 448, 452, 456,)
        self.PARTICLE_OFFSETS = (20, 2, 2, 4, 4, 4, 4, 12, 4, 16, 4, 16, 4, 16, 4, 16, 4, 16, 4, 16, 4, 4, 16, 4, 4, 16, 4, 16, 4, 16, 16,
                                 16, 16, 8, 16, 16, 100, 4, 4, 4,)
        self.DATA_m2from = (self.idFlagsPos, self.parentBone, self.texture, self.geometryModelLength, self.geometryModelOffset,
                            self.recursionModelLength, self.recursionModelOffset, self.fromBlendingToTextureDimensionsColumns,
                            self.emissionSpeed, self.emissionSpeedTimestampKeyFrame, self.speedVar, self.speedVarTimestampKeyFrame,
                            self.verticalRange, self.verticalRangeTimestampKeyFrame, self.horizontalRange,
                            self.horizontalRangeTimestampKeyFrame, self.gravity, self.gravityTimestampKeyFrame, self.lifespan,
                            self.lifespanTimestampKeyFrame, self.lifespanVary, self.emissionRate, self.emissionRateTimestampKeyFrame,
                            self.emissionRateVary, self.emissionAreaLength, self.emissionAreaLengthTimestampKeyFrame,
                            self.emissionAreaWidth, self.emissionAreaWidthTimestampKeyFrame, self.zSource, self.zSourceTimestampKeyFrame,
                            self.colorTrackTimestampKeyFrame, self.alphaTrackTimestampKeyFrame, self.scaleTrackTimestampKeyFrame,
                            self.scaleVary, self.headCellTrackTimestampKeyFrame, self.tailCellTrackTimestampKeyFrame,
                            self.fromTailLengthToFollowScale2, self.nSplinePoints, self.nSplinePointsOffset,
                            self.enabledinInterpolationGlobalId,)
        # Вспомогательные списки/словари
        self.particlesTextures = []  # список id текстур использующихся как частицы
        self.missingTexturesFullPath = []
        self.missingTexturesFlags = []
        self.missingTexturesEq = {}
        self.updatedTextures_m2to = {}
        self.updatedIds = {}

    def paste_btn_m2from(self):
        m2from_path = pyperclip.paste().strip('"')
        if not m2from_path.lower().endswith(".m2"):
            m2from_path = m2from_path + ".m2"
        dpg.set_value("inp_m2from", m2from_path)

    def paste_btn_m2to(self):
        m2to_path = pyperclip.paste().strip('"')
        if not m2to_path.lower().endswith(".m2"):
            m2to_path = m2to_path + ".m2"
        dpg.set_value("inp_m2to", m2to_path)

    def copy_particles_pre(self):
        StatusBar.clear_info()

        dpg.set_value("inp_m2from", dpg.get_value("inp_m2from").strip('"'))
        dpg.set_value("inp_m2to", dpg.get_value("inp_m2to").strip('"'))
        input_m2from = dpg.get_value("inp_m2from")
        input_m2to = dpg.get_value("inp_m2to")

        # Проверяем корректность путей
        if not input_m2from:
            StatusBar.error_info("ERROR: Select the source model.")
            return
        if not os.path.exists(input_m2from):
            StatusBar.error_info(f"{os.path.basename(input_m2from)} not found.")
            return
        if not input_m2to:
            StatusBar.error_info("ERROR: Select the target model.")
            return
        if not os.path.exists(input_m2to):
            StatusBar.error_info(f"{os.path.basename(input_m2to)} not found.")
            return
        if input_m2from == input_m2to:
            StatusBar.error_info("ERROR: You need to choose two different models.")
            return

        # Присваиваем пути для моделей
        self.m2From = input_m2from
        self.m2To = input_m2to
        # Проверяем чекбоксы
        self.saveExistingParticles = dpg.get_value("chk_save_already_exists")
        self.identifyBones = dpg.get_value("chk_identify_bones")
        self.doNotCopyEnabledin = dpg.get_value("chk_do_not_copy_enabledin")
        # Выполняем действия
        try:
            self.calc_n_particles_and_textures_m2from()
            self.reserve_space_for_existing_particle_m2to()
            self.identify_bones()
            self.copy_and_paste_particles()
        except ParticlesCopyError:
            pass

    def calc_n_particles_and_textures_m2from(self):
        with open(self.m2From, "rb") as model_m2from:
            # Проверка на соответствие MD20
            if model_m2from.read(4) != b'MD20':
                StatusBar.error_info("ERROR: The source model must have MD20 structure. Convert it before copying particles.")
                raise ParticlesCopyError

            particles_n_m2from = Binary.get_int_from_bytes(model_m2from, M2Offsets.nParticleEmitters)
            # Выйти если в m2from нет частиц
            if particles_n_m2from == 0:
                StatusBar.error_info("ERROR: There are no particles in source model.")
                raise ParticlesCopyError

            #  Присваиваем количество частиц в источнике и их адреса
            self.nParticlesM2From = particles_n_m2from
            self.particlesAddressM2From = Binary.get_int_from_bytes(model_m2from, M2Offsets.ofsParticleEmitters)
            #  Присваиваем количество текстур в источнике и их адреса
            self.nTexturesM2From = Binary.get_int_from_bytes(model_m2from, M2Offsets.nTextures)
            self.texturesAddressM2From = Binary.get_int_from_bytes(model_m2from, M2Offsets.ofsTextures)

        # *Копируем имеющиеся в целевой модели текстуры
        self.existedTexturesM2To = self.copy_existed_textures_m2to()

    def copy_existed_textures_m2to(self) -> bytes:
        # * Определяем количество текстур и их адреса в целевой модели
        with open(self.m2To, "rb") as model_m2to:
            self.existedTexturesIntM2To = Binary.get_int_from_bytes(model_m2to, M2Offsets.nTextures)
            textures_adress_m2to = Binary.get_int_from_bytes(model_m2to, M2Offsets.ofsTextures)
            # * Копируем текстуры чтобы потом вставить в конец файла и добавить необходимые из целевой модели
            return Binary.read_bytes(model_m2to, textures_adress_m2to, M2Lengths.texture * self.existedTexturesIntM2To)

    def reserve_space_for_existing_particle_m2to(self):
        # В зависимости от чекбокса save_already_existing_particles
        # резервируем место в конце целевой модели под блоки частиц и дописываем 00 до конца строки
        if not self.saveExistingParticles:
            with open(self.m2To, "rb+") as model_m2to:
                Binary.write_zeros(model_m2to)
                self.particlesAdressM2To = Binary.write_to_end(model_m2to, b'\x00' * self.nParticlesM2From * M2Lengths.particle)
                Binary.write_zeros(model_m2to)
                # *Вставляем скопированные текстуры в конец файла
                self.texturesNewAdressM2To = Binary.write_to_end(model_m2to, self.existedTexturesM2To)
                Binary.write_zeros(model_m2to)
                # ! На всякий случай резервируем место для еще nParticlesM2From текстур
                model_m2to.write(b'\x00' * M2Lengths.texture * self.nParticlesM2From)
                # Задаем число частиц и адрес в целевой модели
                Binary.set_int_to_bytes(model_m2to, M2Offsets.nParticleEmitters, self.nParticlesM2From)
                Binary.set_int_to_bytes(model_m2to, M2Offsets.ofsParticleEmitters, self.particlesAdressM2To)
                # *Переназначаем адрес для текстур
                Binary.set_int_to_bytes(model_m2to, M2Offsets.ofsTextures, self.texturesNewAdressM2To)

        elif self.saveExistingParticles:
            with open(self.m2To, "rb+") as model_m2to:
                self.nParticlesM2To = Binary.get_int_from_bytes(model_m2to, M2Offsets.nParticleEmitters)
                if self.nParticlesM2To > 0:
                    Binary.write_zeros(model_m2to)
                    existing_particles_address = Binary.get_int_from_bytes(model_m2to, M2Offsets.ofsParticleEmitters)
                    existing_particles_bytes = Binary.read_bytes(model_m2to, existing_particles_address,
                                                                 M2Lengths.particle * self.nParticlesM2To)
                    existing_particles_new_address = Binary.write_to_end(model_m2to, existing_particles_bytes)
                    self.particlesAdressM2To = Binary.write_to_end(model_m2to, b'\x00' * self.nParticlesM2From * M2Lengths.particle)
                    Binary.write_zeros(model_m2to)
                    # *Вставляем скопированные текстуры в конец файла
                    self.texturesNewAdressM2To = Binary.write_to_end(model_m2to, self.existedTexturesM2To)
                    Binary.write_zeros(model_m2to)
                    # ! На всякий случай резервируем место для еще nParticlesM2From текстур
                    model_m2to.write(b'\x00' * M2Lengths.texture * self.nParticlesM2From)
                    # *Задаем число частиц и адрес в целевой модели
                    particles_n_total = self.nParticlesM2From + self.nParticlesM2To
                    Binary.set_int_to_bytes(model_m2to, M2Offsets.nParticleEmitters, particles_n_total)
                    Binary.set_int_to_bytes(model_m2to, M2Offsets.ofsParticleEmitters, existing_particles_new_address)
                    # *Переназначаем адрес для текстур
                    Binary.set_int_to_bytes(model_m2to, M2Offsets.ofsTextures, self.texturesNewAdressM2To)
                else:
                    StatusBar.error_info("ERROR: There are no particles in target model. Disable checkbox and try again.")
                    raise ParticlesCopyError

    def copy_and_paste_particles(self):
        # ? 1) СОЗДАЕМ СПИСКИ ДЛЯ Timestamps(offsetToTimestampPairs) and Values(offsetToKeyFramePairs) ------------------------------------
        offsetToTimestampPairs_m2from = [[] for _ in range(self.nParticlesM2From)]
        offsetToKeyFramePairs_m2from = [[] for _ in range(self.nParticlesM2From)]
        offsetToTimestampPairs_m2to = [[] for _ in range(self.nParticlesM2From)]
        offsetToKeyFramePairs_m2to = [[] for _ in range(self.nParticlesM2From)]
        numberOfTimestampPairs_m2from = [[] for _ in range(self.nParticlesM2From)]
        numberOfKeyFramePairs_m2from = [[] for _ in range(self.nParticlesM2From)]
        for n in range(self.nParticlesM2From):
            offsetToTimestampPairs_m2from[n] = [[] for _ in range(15)]
            offsetToKeyFramePairs_m2from[n] = [[] for _ in range(15)]
            offsetToTimestampPairs_m2to[n] = [[] for _ in range(15)]
            offsetToKeyFramePairs_m2to[n] = [[] for _ in range(15)]
            numberOfTimestampPairs_m2from[n] = [[] for _ in range(15)]
            numberOfKeyFramePairs_m2from[n] = [[] for _ in range(15)]

        # ? 2) КОПИРУЕМ ЧАСТИЦЫ ИЗ ПЕРВОЙ МОДЕЛИ ------------------------------------------------------------------------------------------
        ALL_subindex = -1
        for i in range(self.nParticlesM2From):
            with open(self.m2From, "rb") as model_m2from:  # * сопоставляем id костей ------------------------------------------------------
                particle_parent_bone_m2from = Binary.get_int_from_bytes(model_m2from, self.particlesAddressM2From +
                                                                        M2Lengths.particle * i + 20, length=2)
                key_bone_id = self.get_key_bone_id(model_m2from, particle_parent_bone_m2from)
                if key_bone_id in self.keyBoneIdsM2From:
                    particle_parent_bone_m2to = self.keyBoneIdsM2To.get(key_bone_id, 0)
                else:
                    particle_parent_bone_m2to = 0

            for i2, _ in enumerate(self.PARTICLE_INDEXES):
                if i2 in (4, 6, 38):
                    with open(self.m2To, "ab") as model_m2to:
                        last_offset = model_m2to.tell()
                        model_m2to.write(b'\x00' * 16)
                        self.DATA_m2from[i2].append(last_offset.to_bytes(4, 'little'))
                elif i2 in (9, 11, 13, 15, 17, 19, 22, 25, 27, 29, 30, 31, 32, 34, 35):
                    ALL_subindex += 1
                    with open(self.m2From, "rb") as model_m2from:
                        numberOfTimestampPairs, numberOfTimestampPairs_bytes = Binary.get_int_and_bytes(model_m2from,
                                                                                                        self.particlesAddressM2From +
                                                                                                        M2Lengths.particle * i +
                                                                                                        self.PARTICLE_INDEXES[i2])
                        numberOfTimestampPairs_m2from[i][ALL_subindex].append(numberOfTimestampPairs)

                        timestamp_offset, timestamp_offset_bytes = Binary.get_int_and_bytes(model_m2from,
                                                                                            self.particlesAddressM2From +
                                                                                            M2Lengths.particle * i +
                                                                                            self.PARTICLE_INDEXES[i2] + 4)
                        numberOfKeyFramePairs, numberOfKeyFramePairs_bytes = Binary.get_int_and_bytes(model_m2from,
                                                                                                      self.particlesAddressM2From +
                                                                                                      M2Lengths.particle * i +
                                                                                                      self.PARTICLE_INDEXES[i2] + 8)
                        numberOfKeyFramePairs_m2from[i][ALL_subindex].append(numberOfKeyFramePairs)

                        values_offset, values_offset_bytes = Binary.get_int_and_bytes(model_m2from,
                                                                                      self.particlesAddressM2From + M2Lengths.particle * i +
                                                                                      self.PARTICLE_INDEXES[i2] + 12)
                    if i2 == 30:
                        with open(self.m2To, "ab") as model_m2to:
                            last_offset1 = Binary.write_to_end(model_m2to, b'\x00' * 2 * numberOfTimestampPairs)
                            offsetToTimestampPairs_m2to[i][ALL_subindex].append(last_offset1)
                            last_offset2 = Binary.write_to_end(model_m2to, b'\x00' * 12 * numberOfKeyFramePairs)
                            offsetToKeyFramePairs_m2to[i][ALL_subindex].append(last_offset2)
                            self.DATA_m2from[i2].append(numberOfTimestampPairs_bytes + last_offset1.to_bytes(4, 'little') +
                                                        numberOfKeyFramePairs_bytes + last_offset2.to_bytes(4, 'little'))
                    elif i2 in (31, 34, 35):
                        with open(self.m2To, "ab") as model_m2to:
                            last_offset1 = Binary.write_to_end(model_m2to, b'\x00' * 2 * numberOfTimestampPairs)
                            offsetToTimestampPairs_m2to[i][ALL_subindex].append(last_offset1)
                            last_offset2 = Binary.write_to_end(model_m2to, b'\x00' * 2 * numberOfKeyFramePairs)
                            offsetToKeyFramePairs_m2to[i][ALL_subindex].append(last_offset2)
                            self.DATA_m2from[i2].append(numberOfTimestampPairs_bytes + last_offset1.to_bytes(4, 'little') +
                                                        numberOfKeyFramePairs_bytes + last_offset2.to_bytes(4, 'little'))
                    elif i2 == 32:
                        with open(self.m2To, "ab") as model_m2to:
                            last_offset1 = Binary.write_to_end(model_m2to, b'\x00' * 2 * numberOfTimestampPairs)
                            offsetToTimestampPairs_m2to[i][ALL_subindex].append(last_offset1)
                            last_offset2 = Binary.write_to_end(model_m2to, b'\x00' * 8 * numberOfKeyFramePairs)
                            offsetToKeyFramePairs_m2to[i][ALL_subindex].append(last_offset2)
                            self.DATA_m2from[i2].append(numberOfTimestampPairs_bytes + last_offset1.to_bytes(4, 'little') +
                                                        numberOfKeyFramePairs_bytes + last_offset2.to_bytes(4, 'little'))
                    else:
                        with open(self.m2To, "ab") as model_m2to:
                            last_offset1 = Binary.write_to_end(model_m2to, b'\x00' * 8 * numberOfTimestampPairs)
                            offsetToTimestampPairs_m2to[i][ALL_subindex].append(last_offset1)
                            last_offset2 = Binary.write_to_end(model_m2to, b'\x00' * 8 * numberOfKeyFramePairs)
                            offsetToKeyFramePairs_m2to[i][ALL_subindex].append(last_offset2)
                            self.DATA_m2from[i2].append(numberOfTimestampPairs_bytes + last_offset1.to_bytes(4, 'little') +
                                                        numberOfKeyFramePairs_bytes + last_offset2.to_bytes(4, 'little'))

                    offsetToTimestampPairs_m2from[i][ALL_subindex].append(timestamp_offset)
                    offsetToKeyFramePairs_m2from[i][ALL_subindex].append(values_offset)
                    if ALL_subindex == 14: ALL_subindex = -1
                else:
                    with open(self.m2From, "rb") as model_m2from:
                        self.DATA_m2from[i2].append(Binary.read_bytes(model_m2from, self.particlesAddressM2From + M2Lengths.particle * i +
                                                                      self.PARTICLE_INDEXES[i2],
                                                                      self.PARTICLE_OFFSETS[i2]))

            # * Присваиваем id костям -----------------------------------------------------------------------------------------------------
            if self.identifyBones:
                self.parentBone[i] = particle_parent_bone_m2to.to_bytes(2, 'little')
                if particle_parent_bone_m2to != 0:  # * если кость не 0 то для частиц нужна новая позиция
                    self.isNeedToUpdateParticlePos.append(particle_parent_bone_m2to)
                else:
                    self.isNeedToUpdateParticlePos.append(False)
            else:
                self.parentBone[i] = b'\x00'
            self.particlesTextures.append(int.from_bytes(self.texture[i], 'little'))

            # Создаем списки для хранения timestamps и values
        Timestamps_Values_bytes = [[] for _ in range(self.nParticlesM2From)]
        Values_Values_bytes = [[] for _ in range(self.nParticlesM2From)]
        Timestamps_Values = [[] for _ in range(self.nParticlesM2From)]
        Values_Values = [[] for _ in range(self.nParticlesM2From)]
        Timestamps_Values_offset_bytes = [[] for _ in range(self.nParticlesM2From)]
        Timestamps_Values_offset = [[] for _ in range(self.nParticlesM2From)]
        Values_Values_offset = [[] for _ in range(self.nParticlesM2From)]
        Timestamps_Final_Timestamp_bytes = [[] for _ in range(self.nParticlesM2From)]
        Values_Final_Val_bytes = [[] for _ in range(self.nParticlesM2From)]
        for n in range(self.nParticlesM2From):
            Timestamps_Values_bytes[n] = [[] for _ in range(15)]
            Values_Values_bytes[n] = [[] for _ in range(15)]
            Timestamps_Values[n] = [[] for _ in range(15)]
            Values_Values[n] = [[] for _ in range(15)]
            Timestamps_Values_offset_bytes[n] = [[] for _ in range(15)]
            Timestamps_Values_offset[n] = [[] for _ in range(15)]
            Values_Values_offset[n] = [[] for _ in range(15)]
            Timestamps_Final_Timestamp_bytes[n] = [[] for _ in range(15)]
            Values_Final_Val_bytes[n] = [[] for _ in range(15)]

        # Ищем и добавляем значения и офсеты timestamps и values
        # Timestamps_Values_offset = Timestamps->Sequence->ofsValues | Values_Values_offset = Values->Sequence->ofsValues
        with open(self.m2From, "rb") as model_m2from:
            for i in range(self.nParticlesM2From):
                for i2 in range(10):
                    Timestamps_nValues_bytes = Binary.read_bytes(model_m2from, int(*offsetToTimestampPairs_m2from[i][i2]))
                    Timestamps_Values_bytes[i][i2].append(Timestamps_nValues_bytes)
                    Timestamps_Values[i][i2].append(int.from_bytes(Timestamps_nValues_bytes, 'little'))
                    Timestamps_nValues_offset_bytes = Binary.read_bytes(model_m2from, int(*offsetToTimestampPairs_m2from[i][i2]) + 4)
                    Timestamps_Values_offset_bytes[i][i2].append(Timestamps_nValues_offset_bytes)
                    Timestamps_Values_offset[i][i2].append(int.from_bytes(Timestamps_nValues_offset_bytes, 'little'))

                    Values_nValues_bytes = Binary.read_bytes(model_m2from, int(*offsetToKeyFramePairs_m2from[i][i2]))
                    Values_Values_bytes[i][i2].append(Values_nValues_bytes)
                    Values_Values[i][i2].append(int.from_bytes(Values_nValues_bytes, 'little'))
                    Values_nValues_offset_bytes = Binary.read_bytes(model_m2from, int(*offsetToKeyFramePairs_m2from[i][i2]) + 4)
                    Values_Values_offset[i][i2].append(int.from_bytes(Values_nValues_offset_bytes, 'little'))

        with open(self.m2From, "rb") as model_m2from:
            for i in range(self.nParticlesM2From):
                for i2 in range(10, 11):
                    Timestamps_nValues_bytes = Binary.read_bytes(model_m2from, int(*offsetToTimestampPairs_m2from[i][i2]),
                                                                 2 * int(*numberOfTimestampPairs_m2from[i][i2]))
                    Timestamps_Values_bytes[i][i2].append(Timestamps_nValues_bytes)
                    Timestamps_Values[i][i2].append(int(*numberOfTimestampPairs_m2from[i][i2]))
                    Timestamps_Values_offset_bytes[i][i2] = offsetToTimestampPairs_m2from[i][i2]
                    Timestamps_Values_offset[i][i2] = offsetToTimestampPairs_m2from[i][i2]

                    Values_nValues_bytes = Binary.read_bytes(model_m2from, int(*offsetToKeyFramePairs_m2from[i][i2]),
                                                             12 * int(*numberOfKeyFramePairs_m2from[i][i2]))
                    Values_Values_bytes[i][i2].append(Values_nValues_bytes)
                    Values_Values[i][i2].append(int(*numberOfKeyFramePairs_m2from[i][i2]))
                    Values_Values_offset[i][i2] = offsetToKeyFramePairs_m2from[i][i2]

        with open(self.m2From, "rb") as model_m2from:
            for i in range(self.nParticlesM2From):
                for i2 in range(11, 12):
                    Timestamps_nValues_bytes = Binary.read_bytes(model_m2from, int(*offsetToTimestampPairs_m2from[i][i2]),
                                                                 2 * int(*numberOfTimestampPairs_m2from[i][i2]))
                    Timestamps_Values_bytes[i][i2].append(Timestamps_nValues_bytes)
                    Timestamps_Values[i][i2].append(int(*numberOfTimestampPairs_m2from[i][i2]))
                    Timestamps_Values_offset_bytes[i][i2] = offsetToTimestampPairs_m2from[i][i2]
                    Timestamps_Values_offset[i][i2] = offsetToTimestampPairs_m2from[i][i2]

                    Values_nValues_bytes = Binary.read_bytes(model_m2from, int(*offsetToKeyFramePairs_m2from[i][i2]),
                                                             2 * int(*numberOfKeyFramePairs_m2from[i][i2]))
                    Values_Values_bytes[i][i2].append(Values_nValues_bytes)
                    Values_Values[i][i2].append(int(*numberOfKeyFramePairs_m2from[i][i2]))
                    Values_Values_offset[i][i2] = offsetToKeyFramePairs_m2from[i][i2]

        with open(self.m2From, "rb") as model_m2from:
            for i in range(self.nParticlesM2From):
                for i2 in range(12, 13):
                    Timestamps_nValues_bytes = Binary.read_bytes(model_m2from, int(*offsetToTimestampPairs_m2from[i][i2]),
                                                                 2 * int(*numberOfTimestampPairs_m2from[i][i2]))
                    Timestamps_Values_bytes[i][i2].append(Timestamps_nValues_bytes)
                    Timestamps_Values[i][i2].append(int(*numberOfTimestampPairs_m2from[i][i2]))
                    Timestamps_Values_offset_bytes[i][i2] = offsetToTimestampPairs_m2from[i][i2]
                    Timestamps_Values_offset[i][i2] = offsetToTimestampPairs_m2from[i][i2]

                    Values_nValues_bytes = Binary.read_bytes(model_m2from, int(*offsetToKeyFramePairs_m2from[i][i2]),
                                                             8 * int(*numberOfKeyFramePairs_m2from[i][i2]))
                    Values_Values_bytes[i][i2].append(Values_nValues_bytes)
                    Values_Values[i][i2].append(int(*numberOfKeyFramePairs_m2from[i][i2]))
                    Values_Values_offset[i][i2] = offsetToKeyFramePairs_m2from[i][i2]

        with open(self.m2From, "rb") as model_m2from:
            for i in range(self.nParticlesM2From):
                for i2 in range(13, 15):
                    Timestamps_nValues_bytes = Binary.read_bytes(model_m2from, int(*offsetToTimestampPairs_m2from[i][i2]),
                                                                 2 * int(*numberOfTimestampPairs_m2from[i][i2]))
                    Timestamps_Values_bytes[i][i2].append(Timestamps_nValues_bytes)
                    Timestamps_Values[i][i2].append(int(*numberOfTimestampPairs_m2from[i][i2]))
                    Timestamps_Values_offset_bytes[i][i2] = offsetToTimestampPairs_m2from[i][i2]
                    Timestamps_Values_offset[i][i2] = offsetToTimestampPairs_m2from[i][i2]

                    Values_nValues_bytes = Binary.read_bytes(model_m2from, int(*offsetToKeyFramePairs_m2from[i][i2]),
                                                             2 * int(*numberOfKeyFramePairs_m2from[i][i2]))
                    Values_Values_bytes[i][i2].append(Values_nValues_bytes)
                    Values_Values[i][i2].append(int(*numberOfKeyFramePairs_m2from[i][i2]))
                    Values_Values_offset[i][i2] = offsetToKeyFramePairs_m2from[i][i2]

        with open(self.m2From, "rb") as model_m2from:
            for i in range(self.nParticlesM2From):
                for i2, _ in enumerate(Timestamps_Values_offset[i]):
                    # Копируем все timestamp->values в лист Timestamps_Final_Timestamp_bytes
                    # и все Values->values в лист Values_Final_Val_bytes
                    if i2 == 10:
                        timestamp_val_bytes = Binary.read_bytes(model_m2from, int(*Timestamps_Values_offset[i][i2]),
                                                                2 * int(*Timestamps_Values[i][i2]))
                        Timestamps_Final_Timestamp_bytes[i][i2].append(timestamp_val_bytes)

                        values_val_bytes = Binary.read_bytes(model_m2from, int(*Values_Values_offset[i][i2]),
                                                             12 * int(*Values_Values[i][i2]))
                        Values_Final_Val_bytes[i][i2].append(values_val_bytes)
                    elif i2 in (11, 13, 14):
                        timestamp_val_bytes = Binary.read_bytes(model_m2from, int(*Timestamps_Values_offset[i][i2]),
                                                                2 * int(*Timestamps_Values[i][i2]))
                        Timestamps_Final_Timestamp_bytes[i][i2].append(timestamp_val_bytes)

                        values_val_bytes = Binary.read_bytes(model_m2from, int(*Values_Values_offset[i][i2]),
                                                             2 * int(*Values_Values[i][i2]))
                        Values_Final_Val_bytes[i][i2].append(values_val_bytes)
                    elif i2 == 12:
                        timestamp_val_bytes = Binary.read_bytes(model_m2from, int(*Timestamps_Values_offset[i][i2]),
                                                                2 * int(*Timestamps_Values[i][i2]))
                        Timestamps_Final_Timestamp_bytes[i][i2].append(timestamp_val_bytes)

                        values_val_bytes = Binary.read_bytes(model_m2from, int(*Values_Values_offset[i][i2]),
                                                             8 * int(*Values_Values[i][i2]))
                        Values_Final_Val_bytes[i][i2].append(values_val_bytes)
                    else:
                        timestamp_val_bytes = Binary.read_bytes(model_m2from, int(*Timestamps_Values_offset[i][i2]),
                                                                4 * int(*Timestamps_Values[i][i2]))
                        Timestamps_Final_Timestamp_bytes[i][i2].append(timestamp_val_bytes)

                        values_val_bytes = Binary.read_bytes(model_m2from, int(*Values_Values_offset[i][i2]),
                                                             4 * int(*Values_Values[i][i2]))
                        Values_Final_Val_bytes[i][i2].append(values_val_bytes)

        # * Копируем недостающие текстуры для частиц из первой модели
        missing_textures_m2from = list(set(self.particlesTextures))
        with open(self.m2From, "rb") as model_m2from:
            for i, missing_texture in enumerate(missing_textures_m2from):
                texture_flag = Binary.get_int_from_bytes(model_m2from,
                                                         self.texturesAddressM2From + M2Lengths.texture * missing_texture + 4)
                self.missingTexturesFlags.append(texture_flag)
                texture_length = Binary.get_int_from_bytes(model_m2from,
                                                           self.texturesAddressM2From + M2Lengths.texture * missing_texture + 8)
                texture_offset = Binary.get_int_from_bytes(model_m2from,
                                                           self.texturesAddressM2From + M2Lengths.texture * missing_texture + 12)
                model_m2from.seek(texture_offset)
                texture_path = model_m2from.read(texture_length)
                self.copy_missing_textures_to_patch_folder(texture_path)  # если текстуры нет в патче копируем ее
                self.missingTexturesFullPath.append(texture_path)
                # Добавляем в словарь связь id текстуры и ее пути
                self.missingTexturesEq[texture_path] = missing_texture

        # Новое число текстур в целевой модели = старые + недостающие
        new_textures_n_m2to = self.existedTexturesIntM2To + len(self.missingTexturesFullPath)

        # * Дописываем недостающие текстуры для частиц во вторую модель
        with open(self.m2To, "rb+") as model_m2to:
            Binary.write_zeros(model_m2to)
            for i, (missing_texture_bytes, flag) in enumerate(zip(self.missingTexturesFullPath, self.missingTexturesFlags)):
                last_texture_adress_m2to = Binary.write_to_end(model_m2to, missing_texture_bytes)
                Binary.write_zeros(model_m2to)
                Binary.write_bytes(model_m2to, self.texturesNewAdressM2To + M2Lengths.texture * (self.existedTexturesIntM2To + i) + 4,
                                   flag.to_bytes(4, 'little'))
                Binary.write_bytes(model_m2to, self.texturesNewAdressM2To + M2Lengths.texture * (self.existedTexturesIntM2To + i) + 8,
                                   len(missing_texture_bytes).to_bytes(4, 'little'))
                Binary.write_bytes(model_m2to, self.texturesNewAdressM2To + M2Lengths.texture * (self.existedTexturesIntM2To + i) + 12,
                                   last_texture_adress_m2to.to_bytes(4, 'little'))

            # Обновляем число текстур в целевой модели
            Binary.write_bytes(model_m2to, M2Offsets.nTextures, new_textures_n_m2to.to_bytes(4, 'little'))

            # Создаем словарь со списком обновленных текстур
            for texture in range(new_textures_n_m2to):
                tex_length = Binary.get_int_from_bytes(model_m2to, self.texturesNewAdressM2To + M2Lengths.texture * texture + 8)
                if tex_length != 0:
                    new_texture_offset = Binary.get_int_from_bytes(model_m2to,
                                                                   self.texturesNewAdressM2To + M2Lengths.texture * texture + 12)
                    new_texture = Binary.read_bytes(model_m2to, new_texture_offset, tex_length)
                    self.updatedTextures_m2to[new_texture] = texture

        # *Переназначаем id текстур в словаре отсутствующих текстур
        for key in self.missingTexturesEq.keys():
            if key in self.updatedTextures_m2to:
                self.updatedIds[self.missingTexturesEq[key]] = self.updatedTextures_m2to[key]

        for t, texture in enumerate(self.texture):
            if int.from_bytes(texture, 'little') in self.updatedIds:
                self.texture[t] = self.updatedIds[int.from_bytes(texture, 'little')].to_bytes(2, 'little')
        # * -------------------------------------------------------------------------------------------------------------------------------
        if not self.doNotCopyEnabledin:
            try:
                self.enabledin()
                enabledin_skipped = False
            except IndexError:
                enabledin_skipped = True
        else:
            enabledin_skipped = False

        # ? 3) ВСТАВЛЯЕМ ЧАСТИЦЫ ВО ВТОРУЮ МОДЕЛЬ -----------------------------------------------------------------------------------------
        with open(self.m2To, "rb+") as model_m2to:
            for i in range(self.nParticlesM2From):
                for i2, _ in enumerate(self.PARTICLE_INDEXES):
                    Binary.write_bytes(model_m2to, self.particlesAdressM2To + M2Lengths.particle * i + self.PARTICLE_INDEXES[i2],
                                       self.DATA_m2from[i2][i])

        with open(self.m2To, "rb+") as model_m2to:
            for i in range(self.nParticlesM2From):
                for i2, _ in enumerate(offsetToTimestampPairs_m2to[i]):
                    if i2 in (10, 11, 12, 13, 14):
                        # Вставляем nValues и ofsValues в Timestamps
                        final_offset1 = model_m2to.seek(0, 2)
                        Binary.write_bytes(model_m2to, final_offset1, bytes(*Timestamps_Final_Timestamp_bytes[i][i2]))
                        Binary.write_bytes(model_m2to, int(*offsetToTimestampPairs_m2to[i][i2]), bytes(*Timestamps_Values_bytes[i][i2]))
                        # Вставляем nValues и ofsValues в Values
                        final_offset2 = model_m2to.seek(0, 2)
                        Binary.write_bytes(model_m2to, final_offset2, bytes(*Values_Final_Val_bytes[i][i2]))
                        Binary.write_bytes(model_m2to, int(*offsetToKeyFramePairs_m2to[i][i2]), bytes(*Values_Values_bytes[i][i2]))
                    else:
                        # Вставляем nValues и ofsValues в Timestamps
                        final_offset1 = model_m2to.seek(0, 2)
                        Binary.write_bytes(model_m2to, final_offset1, bytes(*Timestamps_Final_Timestamp_bytes[i][i2]))
                        Binary.write_bytes(model_m2to, int(*offsetToTimestampPairs_m2to[i][i2]), bytes(*Timestamps_Values_bytes[i][i2]))
                        Binary.write_bytes(model_m2to, int(*offsetToTimestampPairs_m2to[i][i2]) + 4, final_offset1.to_bytes(4, 'little'))
                        # Вставляем nValues и ofsValues в Values
                        final_offset2 = model_m2to.seek(0, 2)
                        Binary.write_bytes(model_m2to, final_offset2, bytes(*Values_Final_Val_bytes[i][i2]))
                        Binary.write_bytes(model_m2to, int(*offsetToKeyFramePairs_m2to[i][i2]), bytes(*Values_Values_bytes[i][i2]))
                        Binary.write_bytes(model_m2to, int(*offsetToKeyFramePairs_m2to[i][i2]) + 4, final_offset2.to_bytes(4, 'little'))

        if self.identifyBones:  # * обновляем позиции частиц ------------------------------------------------------------------------------
            self.update_particle_pos()
        # * Выводим сообщение об успешном копировании -------------------------------------------------------------------------------------
        if enabledin_skipped:
            StatusBar.success_info(str(self.nParticlesM2From) + " particles copied successfully. Total " + str(
                self.nParticlesM2From + self.nParticlesM2To) + " particles in model. 'Enabledin' block not copied because there are "
                                                               "no same animation ID in models.")
        else:
            StatusBar.success_info(str(self.nParticlesM2From) + " particles copied successfully. Total " + str(
                self.nParticlesM2From + self.nParticlesM2To) + " particles in model.")

    def enabledin(self):
        def timestamps_ratio(timestamp_id_: int, timestamp_m2From_: bytes, Animations_id_and_length_m2From_: dict,
                             Animations_id_and_length_m2To_Modified_: dict) -> bytes:
            timestamp_length = len(timestamp_m2From_)
            _Animations_id_and_length_m2From = list(Animations_id_and_length_m2From_.values())
            Animations_id_and_length_m2To_Modified_LIST = list(Animations_id_and_length_m2To_Modified_.values())
            full_timestamp_bytes = b''

            for anim_id in _Animations_id_and_length_m2From:
                if timestamp_id_ == anim_id[0]:
                    sub_index_1 = _Animations_id_and_length_m2From.index(anim_id)
                    sub_index_2 = anim_id.index(anim_id[1])
                    anim_length_m2From = _Animations_id_and_length_m2From[sub_index_1][sub_index_2]
                    anim_length_m2To = Animations_id_and_length_m2To_Modified_LIST[sub_index_1][sub_index_2]
                    Timestamp_MAX = max(anim_length_m2From, anim_length_m2To)
                    Timestamp_MIN = min(anim_length_m2From, anim_length_m2To)
                    if Timestamp_MAX == anim_length_m2From:
                        ratio = Timestamp_MIN / Timestamp_MAX
                    elif Timestamp_MAX == anim_length_m2To:
                        ratio = Timestamp_MAX / Timestamp_MIN
                    for step in range(0, timestamp_length, 4):
                        sliced_timestamp = round(int.from_bytes(timestamp_m2From_[step:step + 4], 'little') * ratio)
                        full_timestamp_bytes += sliced_timestamp.to_bytes(4, 'little')

            return full_timestamp_bytes

        def writing_timestamps_and_values_modelTo(model_m2to_: BinaryIO, i_: int, pos1: int, pos2: int):
            Binary.write_bytes(model_m2to_, self.particlesAdressM2To + M2Lengths.particle * i_ + pos1, self.nAnimationsM2To_bytes)
            enabledin_last_offset = Binary.write_to_end(model_m2to_, b'\x00' * 8 * self.nAnimationsM2To)
            Binary.write_bytes(model_m2to_, self.particlesAdressM2To + M2Lengths.particle * i_ + pos2,
                               enabledin_last_offset.to_bytes(4, byteorder='little'))

        def writing_one_zero_m2To(model_m2to_: BinaryIO, enum_: int, pos: int, n_: int):
            last_Timestamps_Offset_ = Binary.write_to_end(model_m2to_, b'\x00' * 4)
            timestamp_offset = Binary.get_int_from_bytes(model_m2to_, self.particlesAdressM2To + M2Lengths.particle * enum_ + pos)
            Binary.write_bytes(model_m2to_, timestamp_offset + 8 * n_, b'\x01\x00\x00\x00')
            Binary.write_bytes(model_m2to_, timestamp_offset + 8 * n_ + 4, last_Timestamps_Offset_.to_bytes(4, byteorder='little'))

        # Определяем число анимаций и их адрес в m2From -----------------------------------------------------------------------------------
        with open(self.m2From, 'rb') as model_m2from:
            self.nAnimationsM2From = Binary.get_int_from_bytes(model_m2from, M2Offsets.nAnimations)
            self.animationsAdressM2From = Binary.get_int_from_bytes(model_m2from, M2Offsets.ofsAnimations)

        # Создаем необходимые списки
        if self.nAnimationsM2From == 1:
            enabledin_Timestamps_Offsets = []
            enabledin_Timestamps_Values = []
            enabledin_Values_Offsets = []
            enabledin_Values_Values = []
        else:
            enabledin_Timestamps_Offsets = [[] for _ in range(self.nAnimationsM2From)]
            enabledin_Timestamps_Values = [[] for _ in range(self.nAnimationsM2From)]
            enabledin_Values_Offsets = [[] for _ in range(self.nAnimationsM2From)]
            enabledin_Values_Values = [[] for _ in range(self.nAnimationsM2From)]

        enabledin_Timestamps_Keyframes = []
        Animations_id_with_values = []
        Animations_id_and_length_m2From = {}
        All_Animations_id_and_length_m2To = {}
        Animations_id_and_length_m2To_Modified = {}
        Timestamps_Offset_and_n_m2From = [[] for _ in range(self.nParticlesM2From)]
        Values_Offset_and_n_m2From = [[] for _ in range(self.nParticlesM2From)]
        Timestamps_Value_m2From = [[] for _ in range(self.nParticlesM2From)]
        Values_Value_m2From = [[] for _ in range(self.nParticlesM2From)]

        # * Проходим по блокам enabledin
        with open(self.m2From, "rb") as model_m2from:
            for i in range(self.nParticlesM2From):
                enabledin_numberOfTimestampPairs, enabledin_numberOfTimestampPairs_bytes = \
                    Binary.get_int_and_bytes(model_m2from, self.particlesAddressM2From + M2Lengths.particle * i + 460)
                # Если блок enabledin не пустой и больше 1, добавляем число кейфреймов в соответствующий id частицы
                if enabledin_numberOfTimestampPairs_bytes > b'\x01\x00\x00\x00':
                    enabledin_Timestamps_Keyframes.append(enabledin_numberOfTimestampPairs)
                    # Берем значения timestamps и keyframes офсетов и добавляем их в списки
                    offsetToTimestampsPairs = Binary.get_int_from_bytes(model_m2from,
                                                                        self.particlesAddressM2From + M2Lengths.particle * i + 464)
                    offsetToKeyFramePairs = Binary.get_int_from_bytes(model_m2from,
                                                                      self.particlesAddressM2From + M2Lengths.particle * i + 472)
                    sub_Index = 0
                    for n_seq in range(enabledin_numberOfTimestampPairs):
                        # Собираем timestamps
                        timestamps_seq_values = Binary.get_int_from_bytes(model_m2from, offsetToTimestampsPairs + 8 * n_seq)
                        enabledin_Timestamps_Values[i].append(timestamps_seq_values)

                        timestamps_seq_offset = Binary.get_int_from_bytes(model_m2from, offsetToTimestampsPairs + 4 + 8 * n_seq)
                        enabledin_Timestamps_Offsets[i].append(timestamps_seq_offset)
                        # Собираем keyframes
                        values_seq_value = Binary.get_int_from_bytes(model_m2from, offsetToKeyFramePairs + 8 * n_seq)
                        enabledin_Values_Values[i].append(values_seq_value)

                        values_seq_offset = Binary.get_int_from_bytes(model_m2from, offsetToKeyFramePairs + 4 + 8 * n_seq)
                        enabledin_Values_Offsets[i].append(values_seq_offset)

                        value_bytes = Binary.read_bytes(model_m2from, values_seq_offset, length=2)
                        # При условии, что n значений >1 или само значение отлично от 0 добавляем id этих анимаций в словари
                        if values_seq_value > 1 or int.from_bytes(value_bytes, 'little') == 1:
                            Timestamps_Offset_and_n_m2From[i].append([])
                            Values_Offset_and_n_m2From[i].append([])
                            Animations_id_with_values.append(n_seq)
                            Timestamps_Offset_and_n_m2From[i][sub_Index].append(n_seq)
                            Timestamps_Offset_and_n_m2From[i][sub_Index].append(timestamps_seq_offset)
                            Timestamps_Offset_and_n_m2From[i][sub_Index].append(values_seq_value)
                            Values_Offset_and_n_m2From[i][sub_Index].append(n_seq)
                            Values_Offset_and_n_m2From[i][sub_Index].append(values_seq_offset)
                            Values_Offset_and_n_m2From[i][sub_Index].append(values_seq_value)
                            sub_Index += 1
                # Если блок enabledin не пустой (всего 1 анимация) например оружие, щиты
                elif enabledin_numberOfTimestampPairs_bytes == b'\x01\x00\x00\x00':
                    enabledin_Timestamps_Keyframes.append(enabledin_numberOfTimestampPairs)
                    # Берем значения timestamps и keyframes офсетов и добавляем их в списки
                    offsetToTimestampsPairs = Binary.get_int_from_bytes(model_m2from,
                                                                        self.particlesAddressM2From + M2Lengths.particle * i + 464)
                    offsetToKeyFramePairs = Binary.get_int_from_bytes(model_m2from,
                                                                      self.particlesAddressM2From + M2Lengths.particle * i + 472)
                    sub_Index = 0
                    for n_seq in range(enabledin_numberOfTimestampPairs):
                        # Собираем timestamps
                        timestamps_seq_values = Binary.get_int_from_bytes(model_m2from, offsetToTimestampsPairs + 8 * n_seq)
                        enabledin_Timestamps_Values.append(timestamps_seq_values)

                        timestamps_seq_offset = Binary.get_int_from_bytes(model_m2from, offsetToTimestampsPairs + 4 + 8 * n_seq)
                        enabledin_Timestamps_Offsets.append(timestamps_seq_offset)
                        # Собираем keyframes
                        values_seq_value = Binary.get_int_from_bytes(model_m2from, offsetToKeyFramePairs + 8 * n_seq)
                        enabledin_Values_Values.append(values_seq_value)

                        values_seq_offset = Binary.get_int_from_bytes(model_m2from, offsetToKeyFramePairs + 4 + 8 * n_seq)
                        enabledin_Values_Offsets.append(values_seq_offset)

                        value_bytes = Binary.read_bytes(model_m2from, values_seq_offset, length=2)
                        # При условии, что n значений >1 или само значение отлично от 0 добавляем id этих анимаций в словари
                        if values_seq_value > 1 or int.from_bytes(value_bytes, 'little') == 1:
                            Timestamps_Offset_and_n_m2From[i].append([])
                            Values_Offset_and_n_m2From[i].append([])
                            Animations_id_with_values.append(n_seq)
                            Timestamps_Offset_and_n_m2From[i][sub_Index].append(n_seq)
                            Timestamps_Offset_and_n_m2From[i][sub_Index].append(timestamps_seq_offset)
                            Timestamps_Offset_and_n_m2From[i][sub_Index].append(values_seq_value)
                            Values_Offset_and_n_m2From[i][sub_Index].append(n_seq)
                            Values_Offset_and_n_m2From[i][sub_Index].append(values_seq_offset)
                            Values_Offset_and_n_m2From[i][sub_Index].append(values_seq_value)
                            sub_Index += 1
                # Если пустой, то 0
                else:
                    enabledin_Timestamps_Keyframes.append(0)

        # * Создаем множество, чтобы оставить только уникальные id анимаций
        Animations_id_with_values_Unique = sorted(set(Animations_id_with_values))

        # И проходимся по ним и добавляем в словарь
        with open(self.m2From, "rb") as model_m2from:
            for anim in Animations_id_with_values_Unique:
                SubAnimationID = str(
                    Binary.get_int_from_bytes(model_m2from, self.animationsAdressM2From + M2Lengths.animation * anim + 2, length=2))
                animation_id = str(Binary.get_int_from_bytes(model_m2from, self.animationsAdressM2From + M2Lengths.animation * anim,
                                                             length=2)) + "_" + SubAnimationID
                animation_length = Binary.get_int_from_bytes(model_m2from, self.animationsAdressM2From + M2Lengths.animation * anim + 4)

                Animations_id_and_length_m2From[animation_id] = anim, animation_length

        # * Определяем количество анимаций и их адреса в целевой модели
        with open(self.m2To, "rb") as model_m2to:
            self.nAnimationsM2To, self.nAnimationsM2To_bytes = Binary.get_int_and_bytes(model_m2to, M2Offsets.nAnimations)
            self.animationsAdressM2To = Binary.get_int_from_bytes(model_m2to, M2Offsets.ofsAnimations)
            for anim in range(self.nAnimationsM2To):
                SubAnimationID = str(
                    Binary.get_int_from_bytes(model_m2to, self.animationsAdressM2To + M2Lengths.animation * anim + 2, length=2))
                animation_id = str(Binary.get_int_from_bytes(model_m2to, self.animationsAdressM2To + M2Lengths.animation * anim,
                                                             length=2)) + "_" + SubAnimationID
                animation_length = Binary.get_int_from_bytes(model_m2to, self.animationsAdressM2To + M2Lengths.animation * anim + 4)

                All_Animations_id_and_length_m2To[animation_id] = anim, animation_length

        # * Проверяем соответствие id анимаций в обеих моделях
        animations_id_link = {}
        for key in Animations_id_and_length_m2From:
            if key in All_Animations_id_and_length_m2To:
                animations_id_link[Animations_id_and_length_m2From[key][0]] = All_Animations_id_and_length_m2To[key][0]
                Animations_id_and_length_m2To_Modified[key] = All_Animations_id_and_length_m2To[key]

        # Копируем значения Timestamps
        with open(self.m2From, "rb") as model_m2from:
            for i, timestamp in enumerate(Timestamps_Offset_and_n_m2From):
                if timestamp:
                    for i2, timestamp2 in enumerate(timestamp):
                        timestamp_id = timestamp2[0]
                        Timestamps_Value_m2From[i].append([])
                        timestamp_m2From = Binary.read_bytes(model_m2from, timestamp2[1], length=timestamp2[2] * 4)
                        timestamps_from_function = timestamps_ratio(timestamp_id, timestamp_m2From, Animations_id_and_length_m2From,
                                                                    Animations_id_and_length_m2To_Modified)
                        Timestamps_Value_m2From[i][i2].append(timestamp2[0])
                        Timestamps_Value_m2From[i][i2].append(timestamps_from_function)

        # Копируем значения Values
        with open(self.m2From, "rb") as model_m2from:
            for i, Value in enumerate(Values_Offset_and_n_m2From):
                if Value:
                    for i2, Value2 in enumerate(Value):
                        Values_Value_m2From[i].append([])
                        Value_modelFrom = Binary.read_bytes(model_m2from, Value2[1], length=Value2[2])
                        Values_Value_m2From[i][i2].append(Value2[0])
                        Values_Value_m2From[i][i2].append(Value_modelFrom)

        # Прописываем Timestamps и Values в целевой модели
        with open(self.m2To, "rb+") as model_m2to:
            for i, keyframes in enumerate(enabledin_Timestamps_Keyframes):
                if keyframes != 0:
                    # Timestamps
                    writing_timestamps_and_values_modelTo(model_m2to, i, 460, 464)
                    # Values
                    writing_timestamps_and_values_modelTo(model_m2to, i, 468, 472)

        # Прописываем во все Timestamp->Sequence 1 и 0 и Values->Sequence 1 и 0 в целевой модели
        with open(self.m2To, "rb+") as model_m2to:
            for enum, i in enumerate(enabledin_Timestamps_Keyframes):
                if i != 0:
                    for n in range(self.nAnimationsM2To):
                        # Timestamps
                        writing_one_zero_m2To(model_m2to, enum, 464, n)
                        # Values
                        writing_one_zero_m2To(model_m2to, enum, 472, n)

        # Вставляем в имеющиеся id значения Timestamps из списка
        with open(self.m2To, "rb+") as model_m2to:
            for i in range(len(enabledin_Timestamps_Keyframes)):
                for n in range(self.nAnimationsM2To):
                    for timestamp_array in Timestamps_Offset_and_n_m2From[i]:
                        for value in Timestamps_Value_m2From[i]:
                            if timestamp_array[0] in animations_id_link and animations_id_link[timestamp_array[0]] == n and \
                                    timestamp_array[0] == value[0]:
                                last_Timestamps_Offset = Binary.write_to_end(model_m2to, value[1])

                                timestamp_offset1 = Binary.get_int_from_bytes(model_m2to,
                                                                              self.particlesAdressM2To + M2Lengths.particle * i + 464)
                                Binary.write_bytes(model_m2to, timestamp_offset1 + 8 * n,
                                                   timestamp_array[2].to_bytes(4, byteorder='little'))
                                Binary.write_bytes(model_m2to, timestamp_offset1 + 8 * n + 4,
                                                   last_Timestamps_Offset.to_bytes(4, byteorder='little'))

        # Вставляем в имеющиеся id значения Values из списка
        with open(self.m2To, "rb+") as model_m2to:
            for i in range(len(enabledin_Timestamps_Keyframes)):
                for n in range(self.nAnimationsM2To):
                    for value_array in Values_Offset_and_n_m2From[i]:
                        for value2 in Values_Value_m2From[i]:
                            if value_array[0] in animations_id_link and animations_id_link[value_array[0]] == n and \
                                    value_array[0] == value2[0]:
                                last_Timestamps_Offset3 = Binary.write_to_end(model_m2to, value2[1])

                                timestamp_offset4 = Binary.get_int_from_bytes(model_m2to,
                                                                              self.particlesAdressM2To + M2Lengths.particle * i + 472)
                                Binary.write_bytes(model_m2to, timestamp_offset4 + 8 * n,
                                                   value_array[2].to_bytes(4, byteorder='little'))
                                Binary.write_bytes(model_m2to, timestamp_offset4 + 8 * n + 4,
                                                   last_Timestamps_Offset3.to_bytes(4, byteorder='little'))

    def identify_bones(self):
        with open(self.m2From, "rb+") as model_m2from:
            self.nBonesM2From = Binary.get_int_from_bytes(model_m2from, M2Offsets.nBones)
            self.bonesAdressM2From = Binary.get_int_from_bytes(model_m2from, M2Offsets.ofsBones)

            for i in range(self.nBonesM2From):
                kb_id_m2from = Binary.get_int_from_bytes(model_m2from, self.bonesAdressM2From + i * M2Lengths.bone)
                if kb_id_m2from != 4294967295:  # 4294967295 = KBNone(-1)
                    self.keyBoneIdsM2From.append(kb_id_m2from)

        with open(self.m2To, "rb+") as model_m2to:
            self.nBonesM2To = Binary.get_int_from_bytes(model_m2to, M2Offsets.nBones)
            self.bonesAdressM2To = Binary.get_int_from_bytes(model_m2to, M2Offsets.ofsBones)

            for i in range(self.nBonesM2To):
                kb_id_m2to = Binary.get_int_from_bytes(model_m2to, self.bonesAdressM2To + i * M2Lengths.bone)
                if kb_id_m2to != 4294967295:
                    self.keyBoneIdsM2To[kb_id_m2to] = i

    def get_key_bone_id(self, model_: BinaryIO, parent_bone_: int) -> int:
        k_b_id = Binary.get_int_from_bytes(model_, self.bonesAdressM2From + M2Lengths.bone * parent_bone_)
        if k_b_id == 4294967295:
            new_paren_bone = Binary.get_int_from_bytes(model_, self.bonesAdressM2From + M2Lengths.bone * parent_bone_ + 8, length=2)
            if new_paren_bone != 65535:  # 65535 = -1
                new_paren_bone = self.get_key_bone_id(model_, new_paren_bone)
            return new_paren_bone
        return k_b_id

    def update_particle_pos(self):
        with open(self.m2To, "rb+") as model_m2to:
            for i, bone_id in enumerate(self.isNeedToUpdateParticlePos):
                if bone_id:
                    new_pos = Binary.read_bytes(model_m2to, self.bonesAdressM2To + M2Lengths.bone * bone_id + M2Offsets.pivotPoint,
                                                length=M2Lengths.pivotPoint)
                    Binary.write_bytes(model_m2to, self.particlesAdressM2To + M2Lengths.particle * i + 8, new_pos)

    def copy_missing_textures_to_patch_folder(self, missing_texture_: bytes):
        texture_path_ = missing_texture_.decode("utf-8").strip("\x00")
        source_path_ = os.path.join(os.path.dirname(self.m2From), os.path.basename(texture_path_))
        destination_path_ = os.path.join(reg_manager.patchFolder, texture_path_)
        destination_folder = os.path.dirname(destination_path_)
        if not os.path.exists(destination_path_) and os.path.exists(source_path_):
            if not os.path.exists(destination_folder):
                os.mkdir(destination_folder)
            try:
                shutil.copy2(source_path_, destination_path_)
            except OSError:
                pass


def particle_cloner_init():
    StatusBar.clear_info()
    particle_cloner = ParticleCloner()
    particle_cloner.copy_particles_pre()
