from typing import BinaryIO

import dearpygui.dearpygui as dpg
import os
import pyperclip
import shutil

from utils.binary import Binary
from utils.offsets import M2Offset, M2Length
from utils.registry import reg_manager
from utils.statusbar import StatusBar


class ParticlesCopyError(Exception):
    pass


class ParticleCloner:
    def __init__(self):
        self.m2From = None
        self.m2To = None
        self.nPrtclsM2From = 0
        self.nPrtclsM2To = 0
        self.prtclsAddrM2From = 0
        self.prtclsAddrM2To = 0
        self.nTexsM2From = 0
        self.texsAddrM2From = 0
        self.texsNewAddrM2To = 0
        self.nBonesM2From = 0
        self.bonesAddrM2From = 0
        self.nBonesM2To = 0
        self.bonesAddrM2To = 0
        self.keyBoneIdsM2From = []
        self.keyBoneIdsM2To = {}
        self.isNeedToUpdateParticlePos = []
        self.existedTexsIntM2To = None
        self.existedTexM2To = None
        self.saveExistingParticles = False
        self.identifyBones = True
        self.doNotCopyEnabledin = False
        # для enabledin
        self.nAnimsM2From = 0
        self.animsAddrM2From = 0
        self.nAnimsM2To = 0
        self.nAnimsM2To_bytes = None
        self.animsAddrM2To = 0
        # Название полей из 010Editor
        self.idFlagsPos = []
        self.parentBone = []
        self.texs = []
        self.geometryModelLength = []
        self.geometryModelOffset = []
        self.recursionModelLength = []
        self.recursionModelOffset = []
        self.fromBlendingToTextureDimensionsColumns = []
        self.emissionSpeed = []
        self.emissionSpeedTsKf = []
        self.speedVar = []
        self.speedVarTsKf = []
        self.verticalRange = []
        self.verticalRangeTsKf = []
        self.horizontalRange = []
        self.horizontalRangeTsKf = []
        self.gravity = []
        self.gravityTsKf = []
        self.lifespan = []
        self.lifespanTsKf = []
        self.lifespanVary = []
        self.emissionRate = []
        self.emissionRateTsKf = []
        self.emissionRateVary = []
        self.emissionAreaLength = []
        self.emissionAreaLengthTsKf = []
        self.emissionAreaWidth = []
        self.emissionAreaWidthTsKf = []
        self.zSource = []
        self.zSourceTsKf = []
        self.colorTrackTsKf = []
        self.alphaTrackTsKf = []
        self.scaleTrackTsKf = []
        self.scaleVary = []
        self.headCellTrackTsKf = []
        self.tailCellTrackTsKf = []
        self.fromTailLengthToFollowScale2 = []
        self.nSplinePoints = []
        self.nSplinePointsOffset = []
        self.enabledinInterpGlobalId = []
        # Индексы/офсеты
        self.PRTCL_IDXS = (0, 20, 22, 24, 28, 32, 36, 40, 52, 56, 72, 76, 92, 96, 112, 116, 132, 136, 152, 156, 172, 176, 180, 196, 200,
                           204, 220, 224, 240, 244, 260, 276, 292, 308, 316, 332, 348, 448, 452, 456,)
        self.PRTCL_OFFS = (20, 2, 2, 4, 4, 4, 4, 12, 4, 16, 4, 16, 4, 16, 4, 16, 4, 16, 4, 16, 4, 4, 16, 4, 4, 16, 4, 16, 4, 16, 16, 16,
                           16, 8, 16, 16, 100, 4, 4, 4,)
        self.DATA_m2from = (self.idFlagsPos, self.parentBone, self.texs, self.geometryModelLength, self.geometryModelOffset,
                            self.recursionModelLength, self.recursionModelOffset, self.fromBlendingToTextureDimensionsColumns,
                            self.emissionSpeed, self.emissionSpeedTsKf, self.speedVar, self.speedVarTsKf, self.verticalRange,
                            self.verticalRangeTsKf, self.horizontalRange, self.horizontalRangeTsKf, self.gravity, self.gravityTsKf,
                            self.lifespan, self.lifespanTsKf, self.lifespanVary, self.emissionRate, self.emissionRateTsKf,
                            self.emissionRateVary, self.emissionAreaLength, self.emissionAreaLengthTsKf, self.emissionAreaWidth,
                            self.emissionAreaWidthTsKf, self.zSource, self.zSourceTsKf, self.colorTrackTsKf, self.alphaTrackTsKf,
                            self.scaleTrackTsKf, self.scaleVary, self.headCellTrackTsKf, self.tailCellTrackTsKf,
                            self.fromTailLengthToFollowScale2, self.nSplinePoints, self.nSplinePointsOffset, self.enabledinInterpGlobalId,)
        # Вспомогательные списки/словари
        self.prtclsTexs = []  # список id текстур использующихся как частицы
        self.missingTexsFullPath = []
        self.missingTexsFlags = []
        self.missingTexsEq = {}
        self.updatedTexs_m2to = {}
        self.updatedIds = {}

    def paste_btn_m2from(self):
        m2from_path = pyperclip.paste().strip('"')
        if not m2from_path.lower().endswith(".m2"):
            m2from_path = m2from_path + ".m2"
        dpg.set_value("inp_cloner_m2from", m2from_path)

    def paste_btn_m2to(self):
        m2to_path = pyperclip.paste().strip('"')
        if not m2to_path.lower().endswith(".m2"):
            m2to_path = m2to_path + ".m2"
        dpg.set_value("inp_cloner_m2to", m2to_path)

    def copy_particles_pre(self):
        StatusBar.clear_info()

        dpg.set_value("inp_cloner_m2from", dpg.get_value("inp_cloner_m2from").strip('"'))
        dpg.set_value("inp_cloner_m2to", dpg.get_value("inp_cloner_m2to").strip('"'))
        input_m2from = dpg.get_value("inp_cloner_m2from")
        input_m2to = dpg.get_value("inp_cloner_m2to")

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

            particles_n_m2from = Binary.get_int_from_bytes(model_m2from, M2Offset.nPrtclEmitters)
            # Выйти если в m2from нет частиц
            if particles_n_m2from == 0:
                StatusBar.error_info("ERROR: There are no particles in source model.")
                raise ParticlesCopyError

            #  Присваиваем количество частиц в источнике и их адреса
            self.nPrtclsM2From = particles_n_m2from
            self.prtclsAddrM2From = Binary.get_int_from_bytes(model_m2from, M2Offset.ofsPrtclEmitters)
            #  Присваиваем количество текстур в источнике и их адреса
            self.nTexsM2From = Binary.get_int_from_bytes(model_m2from, M2Offset.nTexs)
            self.texsAddrM2From = Binary.get_int_from_bytes(model_m2from, M2Offset.ofsTexs)

        # *Копируем имеющиеся в целевой модели текстуры
        self.existedTexM2To = self.copy_existed_textures_m2to()

    def copy_existed_textures_m2to(self) -> bytes:
        # * Определяем количество текстур и их адреса в целевой модели
        with open(self.m2To, "rb") as model_m2to:
            self.existedTexsIntM2To = Binary.get_int_from_bytes(model_m2to, M2Offset.nTexs)
            textures_adress_m2to = Binary.get_int_from_bytes(model_m2to, M2Offset.ofsTexs)
            # * Копируем текстуры чтобы потом вставить в конец файла и добавить необходимые из целевой модели
            return Binary.read_bytes(model_m2to, textures_adress_m2to, M2Length.texture * self.existedTexsIntM2To)

    def reserve_space_for_existing_particle_m2to(self):
        # В зависимости от чекбокса saveExistingParticles
        # резервируем место в конце целевой модели под блоки частиц и дописываем 00 до конца строки
        if not self.saveExistingParticles:
            with open(self.m2To, "rb+") as model_m2to:
                Binary.write_zeros(model_m2to)
                self.prtclsAddrM2To = Binary.write_to_end(model_m2to, b'\x00' * self.nPrtclsM2From * M2Length.prtcl)
                Binary.write_zeros(model_m2to)
                # *Вставляем скопированные текстуры в конец файла
                self.texsNewAddrM2To = Binary.write_to_end(model_m2to, self.existedTexM2To)
                Binary.write_zeros(model_m2to)
                # ! На всякий случай резервируем место для еще nParticlesM2From текстур
                model_m2to.write(b'\x00' * M2Length.texture * self.nPrtclsM2From)
                # Задаем число частиц и адрес в целевой модели
                Binary.set_int_to_bytes(model_m2to, M2Offset.nPrtclEmitters, self.nPrtclsM2From)
                Binary.set_int_to_bytes(model_m2to, M2Offset.ofsPrtclEmitters, self.prtclsAddrM2To)
                # *Переназначаем адрес для текстур
                Binary.set_int_to_bytes(model_m2to, M2Offset.ofsTexs, self.texsNewAddrM2To)

        elif self.saveExistingParticles:
            with open(self.m2To, "rb+") as model_m2to:
                self.nPrtclsM2To = Binary.get_int_from_bytes(model_m2to, M2Offset.nPrtclEmitters)
                if self.nPrtclsM2To > 0:
                    Binary.write_zeros(model_m2to)
                    existing_particles_address = Binary.get_int_from_bytes(model_m2to, M2Offset.ofsPrtclEmitters)
                    existing_particles_bytes = Binary.read_bytes(model_m2to, existing_particles_address,
                                                                 M2Length.prtcl * self.nPrtclsM2To)
                    existing_particles_new_address = Binary.write_to_end(model_m2to, existing_particles_bytes)
                    self.prtclsAddrM2To = Binary.write_to_end(model_m2to, b'\x00' * self.nPrtclsM2From * M2Length.prtcl)
                    Binary.write_zeros(model_m2to)
                    # *Вставляем скопированные текстуры в конец файла
                    self.texsNewAddrM2To = Binary.write_to_end(model_m2to, self.existedTexM2To)
                    Binary.write_zeros(model_m2to)
                    # ! На всякий случай резервируем место для еще nParticlesM2From текстур
                    model_m2to.write(b'\x00' * M2Length.texture * self.nPrtclsM2From)
                    # *Задаем число частиц и адрес в целевой модели
                    particles_n_total = self.nPrtclsM2From + self.nPrtclsM2To
                    Binary.set_int_to_bytes(model_m2to, M2Offset.nPrtclEmitters, particles_n_total)
                    Binary.set_int_to_bytes(model_m2to, M2Offset.ofsPrtclEmitters, existing_particles_new_address)
                    # *Переназначаем адрес для текстур
                    Binary.set_int_to_bytes(model_m2to, M2Offset.ofsTexs, self.texsNewAddrM2To)
                else:
                    StatusBar.error_info("ERROR: There are no particles in target model. Disable checkbox and try again.")
                    raise ParticlesCopyError

    def copy_and_paste_particles(self):
        # ? 1) СОЗДАЕМ СПИСКИ ДЛЯ Timestamps(offsetToTimestampPairs) and Values(offsetToKeyFramePairs) ------------------------------------
        offsetToTsPairs_m2from = [[] for _ in range(self.nPrtclsM2From)]
        offsetToKfPairs_m2from = [[] for _ in range(self.nPrtclsM2From)]
        offsetToTsPairs_m2to = [[] for _ in range(self.nPrtclsM2From)]
        offsetToKfPairs_m2to = [[] for _ in range(self.nPrtclsM2From)]
        numbOfTsPairs_m2from = [[] for _ in range(self.nPrtclsM2From)]
        numbOfKfPairs_m2from = [[] for _ in range(self.nPrtclsM2From)]
        for n in range(self.nPrtclsM2From):
            offsetToTsPairs_m2from[n] = [[] for _ in range(15)]
            offsetToKfPairs_m2from[n] = [[] for _ in range(15)]
            offsetToTsPairs_m2to[n] = [[] for _ in range(15)]
            offsetToKfPairs_m2to[n] = [[] for _ in range(15)]
            numbOfTsPairs_m2from[n] = [[] for _ in range(15)]
            numbOfKfPairs_m2from[n] = [[] for _ in range(15)]

        # ? 2) КОПИРУЕМ ЧАСТИЦЫ ИЗ ПЕРВОЙ МОДЕЛИ ------------------------------------------------------------------------------------------
        ALL_subindex = -1
        for i in range(self.nPrtclsM2From):
            with open(self.m2From, "rb") as model_m2from:  # * сопоставляем id костей ------------------------------------------------------
                particle_parent_bone_m2from = Binary.get_int_from_bytes(model_m2from, self.prtclsAddrM2From + M2Length.prtcl * i + 20,
                                                                        length=2)
                key_bone_id = self.get_key_bone_id(model_m2from, particle_parent_bone_m2from)
                if key_bone_id in self.keyBoneIdsM2From:
                    particle_parent_bone_m2to = self.keyBoneIdsM2To.get(key_bone_id, 0)
                else:
                    particle_parent_bone_m2to = 0

            for i2, _ in enumerate(self.PRTCL_IDXS):
                if i2 in (4, 6, 38):
                    with open(self.m2To, "ab") as model_m2to:
                        last_offset = model_m2to.tell()
                        model_m2to.write(b'\x00' * 16)
                        self.DATA_m2from[i2].append(last_offset.to_bytes(4, 'little'))
                elif i2 in (9, 11, 13, 15, 17, 19, 22, 25, 27, 29, 30, 31, 32, 34, 35):
                    ALL_subindex += 1
                    with open(self.m2From, "rb") as model_m2from:
                        numbOfTsPairs, numbOfTsPairs_bytes = Binary.get_int_and_bytes(model_m2from, self.prtclsAddrM2From +
                                                                                      M2Length.prtcl * i + self.PRTCL_IDXS[i2])
                        numbOfTsPairs_m2from[i][ALL_subindex].append(numbOfTsPairs)

                        ts_offset, ts_offset_bytes = Binary.get_int_and_bytes(model_m2from, self.prtclsAddrM2From +
                                                                              M2Length.prtcl * i + self.PRTCL_IDXS[i2] + 4)
                        numbOfKfPairs, numbOfKfPairs_bytes = Binary.get_int_and_bytes(model_m2from, self.prtclsAddrM2From +
                                                                                      M2Length.prtcl * i + self.PRTCL_IDXS[i2] + 8)
                        numbOfKfPairs_m2from[i][ALL_subindex].append(numbOfKfPairs)

                        val_offset, val_offset_bytes = Binary.get_int_and_bytes(model_m2from, self.prtclsAddrM2From +
                                                                                M2Length.prtcl * i + self.PRTCL_IDXS[i2] + 12)
                    if i2 == 30:
                        with open(self.m2To, "ab") as model_m2to:
                            last_offset1 = Binary.write_to_end(model_m2to, b'\x00' * 2 * numbOfTsPairs)
                            offsetToTsPairs_m2to[i][ALL_subindex].append(last_offset1)
                            last_offset2 = Binary.write_to_end(model_m2to, b'\x00' * 12 * numbOfKfPairs)
                            offsetToKfPairs_m2to[i][ALL_subindex].append(last_offset2)
                            self.DATA_m2from[i2].append(numbOfTsPairs_bytes + last_offset1.to_bytes(4, 'little') +
                                                        numbOfKfPairs_bytes + last_offset2.to_bytes(4, 'little'))
                    elif i2 in (31, 34, 35):
                        with open(self.m2To, "ab") as model_m2to:
                            last_offset1 = Binary.write_to_end(model_m2to, b'\x00' * 2 * numbOfTsPairs)
                            offsetToTsPairs_m2to[i][ALL_subindex].append(last_offset1)
                            last_offset2 = Binary.write_to_end(model_m2to, b'\x00' * 2 * numbOfKfPairs)
                            offsetToKfPairs_m2to[i][ALL_subindex].append(last_offset2)
                            self.DATA_m2from[i2].append(numbOfTsPairs_bytes + last_offset1.to_bytes(4, 'little') +
                                                        numbOfKfPairs_bytes + last_offset2.to_bytes(4, 'little'))
                    elif i2 == 32:
                        with open(self.m2To, "ab") as model_m2to:
                            last_offset1 = Binary.write_to_end(model_m2to, b'\x00' * 2 * numbOfTsPairs)
                            offsetToTsPairs_m2to[i][ALL_subindex].append(last_offset1)
                            last_offset2 = Binary.write_to_end(model_m2to, b'\x00' * 8 * numbOfKfPairs)
                            offsetToKfPairs_m2to[i][ALL_subindex].append(last_offset2)
                            self.DATA_m2from[i2].append(numbOfTsPairs_bytes + last_offset1.to_bytes(4, 'little') +
                                                        numbOfKfPairs_bytes + last_offset2.to_bytes(4, 'little'))
                    else:
                        with open(self.m2To, "ab") as model_m2to:
                            last_offset1 = Binary.write_to_end(model_m2to, b'\x00' * 8 * numbOfTsPairs)
                            offsetToTsPairs_m2to[i][ALL_subindex].append(last_offset1)
                            last_offset2 = Binary.write_to_end(model_m2to, b'\x00' * 8 * numbOfKfPairs)
                            offsetToKfPairs_m2to[i][ALL_subindex].append(last_offset2)
                            self.DATA_m2from[i2].append(numbOfTsPairs_bytes + last_offset1.to_bytes(4, 'little') +
                                                        numbOfKfPairs_bytes + last_offset2.to_bytes(4, 'little'))

                    offsetToTsPairs_m2from[i][ALL_subindex].append(ts_offset)
                    offsetToKfPairs_m2from[i][ALL_subindex].append(val_offset)
                    if ALL_subindex == 14: ALL_subindex = -1
                else:
                    with open(self.m2From, "rb") as model_m2from:
                        self.DATA_m2from[i2].append(Binary.read_bytes(model_m2from, self.prtclsAddrM2From + M2Length.prtcl * i +
                                                                      self.PRTCL_IDXS[i2], self.PRTCL_OFFS[i2]))

            # * Присваиваем id костям -----------------------------------------------------------------------------------------------------
            if self.identifyBones:
                self.parentBone[i] = particle_parent_bone_m2to.to_bytes(2, 'little')
                if particle_parent_bone_m2to != 0:  # * если кость не 0 то для частиц нужна новая позиция
                    self.isNeedToUpdateParticlePos.append(particle_parent_bone_m2to)
                else:
                    self.isNeedToUpdateParticlePos.append(False)
            else:
                self.parentBone[i] = b'\x00'
            self.prtclsTexs.append(int.from_bytes(self.texs[i], 'little'))

        # Создаем списки для хранения timestamps и values
        Ts_Val_bytes = [[] for _ in range(self.nPrtclsM2From)]
        Val_Val_bytes = [[] for _ in range(self.nPrtclsM2From)]
        Ts_Val = [[] for _ in range(self.nPrtclsM2From)]
        Val_Val = [[] for _ in range(self.nPrtclsM2From)]
        Ts_Val_offset_bytes = [[] for _ in range(self.nPrtclsM2From)]
        Ts_Val_offset = [[] for _ in range(self.nPrtclsM2From)]
        Val_Val_offset = [[] for _ in range(self.nPrtclsM2From)]
        Ts_Final_Ts_bytes = [[] for _ in range(self.nPrtclsM2From)]
        Val_Final_Val_bytes = [[] for _ in range(self.nPrtclsM2From)]
        for n in range(self.nPrtclsM2From):
            Ts_Val_bytes[n] = [[] for _ in range(15)]
            Val_Val_bytes[n] = [[] for _ in range(15)]
            Ts_Val[n] = [[] for _ in range(15)]
            Val_Val[n] = [[] for _ in range(15)]
            Ts_Val_offset_bytes[n] = [[] for _ in range(15)]
            Ts_Val_offset[n] = [[] for _ in range(15)]
            Val_Val_offset[n] = [[] for _ in range(15)]
            Ts_Final_Ts_bytes[n] = [[] for _ in range(15)]
            Val_Final_Val_bytes[n] = [[] for _ in range(15)]

        # Ищем и добавляем значения и офсеты timestamps и values
        # Ts_Val_offset = Timestamps->Sequence->ofsValues | Val_Val_offset = Values->Sequence->ofsValues
        with open(self.m2From, "rb") as model_m2from:
            for i in range(self.nPrtclsM2From):
                for i2 in range(10):
                    Ts_nVal_bytes = Binary.read_bytes(model_m2from, int(*offsetToTsPairs_m2from[i][i2]))
                    Ts_Val_bytes[i][i2].append(Ts_nVal_bytes)
                    Ts_Val[i][i2].append(int.from_bytes(Ts_nVal_bytes, 'little'))
                    Ts_nVal_offset_bytes = Binary.read_bytes(model_m2from, int(*offsetToTsPairs_m2from[i][i2]) + 4)
                    Ts_Val_offset_bytes[i][i2].append(Ts_nVal_offset_bytes)
                    Ts_Val_offset[i][i2].append(int.from_bytes(Ts_nVal_offset_bytes, 'little'))

                    Val_nVal_bytes = Binary.read_bytes(model_m2from, int(*offsetToKfPairs_m2from[i][i2]))
                    Val_Val_bytes[i][i2].append(Val_nVal_bytes)
                    Val_Val[i][i2].append(int.from_bytes(Val_nVal_bytes, 'little'))
                    Val_nVal_offset_bytes = Binary.read_bytes(model_m2from, int(*offsetToKfPairs_m2from[i][i2]) + 4)
                    Val_Val_offset[i][i2].append(int.from_bytes(Val_nVal_offset_bytes, 'little'))

        with open(self.m2From, "rb") as model_m2from:
            for i in range(self.nPrtclsM2From):
                for i2 in range(10, 11):
                    Ts_nVal_bytes = Binary.read_bytes(model_m2from, int(*offsetToTsPairs_m2from[i][i2]),
                                                      2 * int(*numbOfTsPairs_m2from[i][i2]))
                    Ts_Val_bytes[i][i2].append(Ts_nVal_bytes)
                    Ts_Val[i][i2].append(int(*numbOfTsPairs_m2from[i][i2]))
                    Ts_Val_offset_bytes[i][i2] = offsetToTsPairs_m2from[i][i2]
                    Ts_Val_offset[i][i2] = offsetToTsPairs_m2from[i][i2]

                    Val_nVal_bytes = Binary.read_bytes(model_m2from, int(*offsetToKfPairs_m2from[i][i2]),
                                                       12 * int(*numbOfKfPairs_m2from[i][i2]))
                    Val_Val_bytes[i][i2].append(Val_nVal_bytes)
                    Val_Val[i][i2].append(int(*numbOfKfPairs_m2from[i][i2]))
                    Val_Val_offset[i][i2] = offsetToKfPairs_m2from[i][i2]

        with open(self.m2From, "rb") as model_m2from:
            for i in range(self.nPrtclsM2From):
                for i2 in range(11, 12):
                    Ts_nVal_bytes = Binary.read_bytes(model_m2from, int(*offsetToTsPairs_m2from[i][i2]),
                                                      2 * int(*numbOfTsPairs_m2from[i][i2]))
                    Ts_Val_bytes[i][i2].append(Ts_nVal_bytes)
                    Ts_Val[i][i2].append(int(*numbOfTsPairs_m2from[i][i2]))
                    Ts_Val_offset_bytes[i][i2] = offsetToTsPairs_m2from[i][i2]
                    Ts_Val_offset[i][i2] = offsetToTsPairs_m2from[i][i2]

                    Val_nVal_bytes = Binary.read_bytes(model_m2from, int(*offsetToKfPairs_m2from[i][i2]),
                                                       2 * int(*numbOfKfPairs_m2from[i][i2]))
                    Val_Val_bytes[i][i2].append(Val_nVal_bytes)
                    Val_Val[i][i2].append(int(*numbOfKfPairs_m2from[i][i2]))
                    Val_Val_offset[i][i2] = offsetToKfPairs_m2from[i][i2]

        with open(self.m2From, "rb") as model_m2from:
            for i in range(self.nPrtclsM2From):
                for i2 in range(12, 13):
                    Ts_nVal_bytes = Binary.read_bytes(model_m2from, int(*offsetToTsPairs_m2from[i][i2]),
                                                      2 * int(*numbOfTsPairs_m2from[i][i2]))
                    Ts_Val_bytes[i][i2].append(Ts_nVal_bytes)
                    Ts_Val[i][i2].append(int(*numbOfTsPairs_m2from[i][i2]))
                    Ts_Val_offset_bytes[i][i2] = offsetToTsPairs_m2from[i][i2]
                    Ts_Val_offset[i][i2] = offsetToTsPairs_m2from[i][i2]

                    Val_nVal_bytes = Binary.read_bytes(model_m2from, int(*offsetToKfPairs_m2from[i][i2]),
                                                       8 * int(*numbOfKfPairs_m2from[i][i2]))
                    Val_Val_bytes[i][i2].append(Val_nVal_bytes)
                    Val_Val[i][i2].append(int(*numbOfKfPairs_m2from[i][i2]))
                    Val_Val_offset[i][i2] = offsetToKfPairs_m2from[i][i2]

        with open(self.m2From, "rb") as model_m2from:
            for i in range(self.nPrtclsM2From):
                for i2 in range(13, 15):
                    Ts_nVal_bytes = Binary.read_bytes(model_m2from, int(*offsetToTsPairs_m2from[i][i2]),
                                                      2 * int(*numbOfTsPairs_m2from[i][i2]))
                    Ts_Val_bytes[i][i2].append(Ts_nVal_bytes)
                    Ts_Val[i][i2].append(int(*numbOfTsPairs_m2from[i][i2]))
                    Ts_Val_offset_bytes[i][i2] = offsetToTsPairs_m2from[i][i2]
                    Ts_Val_offset[i][i2] = offsetToTsPairs_m2from[i][i2]

                    Val_nVal_bytes = Binary.read_bytes(model_m2from, int(*offsetToKfPairs_m2from[i][i2]),
                                                       2 * int(*numbOfKfPairs_m2from[i][i2]))
                    Val_Val_bytes[i][i2].append(Val_nVal_bytes)
                    Val_Val[i][i2].append(int(*numbOfKfPairs_m2from[i][i2]))
                    Val_Val_offset[i][i2] = offsetToKfPairs_m2from[i][i2]

        with open(self.m2From, "rb") as model_m2from:
            for i in range(self.nPrtclsM2From):
                for i2, _ in enumerate(Ts_Val_offset[i]):
                    # Копируем все timestamp->values в лист Ts_Final_Ts_bytes и все Values->values в лист Values_Final_Val_bytes
                    if i2 == 10:
                        ts_val_bytes = Binary.read_bytes(model_m2from, int(*Ts_Val_offset[i][i2]), 2 * int(*Ts_Val[i][i2]))
                        Ts_Final_Ts_bytes[i][i2].append(ts_val_bytes)

                        values_val_bytes = Binary.read_bytes(model_m2from, int(*Val_Val_offset[i][i2]), 12 * int(*Val_Val[i][i2]))
                        Val_Final_Val_bytes[i][i2].append(values_val_bytes)
                    elif i2 in (11, 13, 14):
                        ts_val_bytes = Binary.read_bytes(model_m2from, int(*Ts_Val_offset[i][i2]), 2 * int(*Ts_Val[i][i2]))
                        Ts_Final_Ts_bytes[i][i2].append(ts_val_bytes)

                        values_val_bytes = Binary.read_bytes(model_m2from, int(*Val_Val_offset[i][i2]), 2 * int(*Val_Val[i][i2]))
                        Val_Final_Val_bytes[i][i2].append(values_val_bytes)
                    elif i2 == 12:
                        ts_val_bytes = Binary.read_bytes(model_m2from, int(*Ts_Val_offset[i][i2]), 2 * int(*Ts_Val[i][i2]))
                        Ts_Final_Ts_bytes[i][i2].append(ts_val_bytes)

                        values_val_bytes = Binary.read_bytes(model_m2from, int(*Val_Val_offset[i][i2]), 8 * int(*Val_Val[i][i2]))
                        Val_Final_Val_bytes[i][i2].append(values_val_bytes)
                    else:
                        ts_val_bytes = Binary.read_bytes(model_m2from, int(*Ts_Val_offset[i][i2]), 4 * int(*Ts_Val[i][i2]))
                        Ts_Final_Ts_bytes[i][i2].append(ts_val_bytes)

                        values_val_bytes = Binary.read_bytes(model_m2from, int(*Val_Val_offset[i][i2]), 4 * int(*Val_Val[i][i2]))
                        Val_Final_Val_bytes[i][i2].append(values_val_bytes)

        # * Копируем недостающие текстуры для частиц из первой модели
        missing_texs_m2from = list(set(self.prtclsTexs))
        with open(self.m2From, "rb") as model_m2from:
            for i, missing_tex in enumerate(missing_texs_m2from):
                tex_flag = Binary.get_int_from_bytes(model_m2from, self.texsAddrM2From + M2Length.texture * missing_tex + 4)
                self.missingTexsFlags.append(tex_flag)
                tex_len = Binary.get_int_from_bytes(model_m2from, self.texsAddrM2From + M2Length.texture * missing_tex + 8)
                tex_offset = Binary.get_int_from_bytes(model_m2from, self.texsAddrM2From + M2Length.texture * missing_tex + 12)
                model_m2from.seek(tex_offset)
                tex_path = model_m2from.read(tex_len)
                self.copy_missing_textures_to_patch_folder(tex_path)  # если текстуры нет в патче копируем ее
                self.missingTexsFullPath.append(tex_path)
                # Добавляем в словарь связь id текстуры и ее пути
                self.missingTexsEq[tex_path] = missing_tex

        # Новое число текстур в целевой модели = старые + недостающие
        new_texs_n_m2to = self.existedTexsIntM2To + len(self.missingTexsFullPath)

        # * Дописываем недостающие текстуры для частиц во вторую модель
        with open(self.m2To, "rb+") as model_m2to:
            Binary.write_zeros(model_m2to)
            for i, (missing_texture_bytes, flag) in enumerate(zip(self.missingTexsFullPath, self.missingTexsFlags)):
                last_texture_adress_m2to = Binary.write_to_end(model_m2to, missing_texture_bytes)
                Binary.write_zeros(model_m2to)
                Binary.write_bytes(model_m2to, self.texsNewAddrM2To + M2Length.texture * (self.existedTexsIntM2To + i) + 4,
                                   flag.to_bytes(4, 'little'))
                Binary.write_bytes(model_m2to, self.texsNewAddrM2To + M2Length.texture * (self.existedTexsIntM2To + i) + 8,
                                   len(missing_texture_bytes).to_bytes(4, 'little'))
                Binary.write_bytes(model_m2to, self.texsNewAddrM2To + M2Length.texture * (self.existedTexsIntM2To + i) + 12,
                                   last_texture_adress_m2to.to_bytes(4, 'little'))

            # Обновляем число текстур в целевой модели
            Binary.write_bytes(model_m2to, M2Offset.nTexs, new_texs_n_m2to.to_bytes(4, 'little'))

            # Создаем словарь со списком обновленных текстур
            for texture in range(new_texs_n_m2to):
                tex_length = Binary.get_int_from_bytes(model_m2to, self.texsNewAddrM2To + M2Length.texture * texture + 8)
                if tex_length != 0:
                    new_texture_offset = Binary.get_int_from_bytes(model_m2to, self.texsNewAddrM2To + M2Length.texture * texture + 12)
                    new_texture = Binary.read_bytes(model_m2to, new_texture_offset, tex_length)
                    self.updatedTexs_m2to[new_texture] = texture

        # *Переназначаем id текстур в словаре отсутствующих текстур
        for key in self.missingTexsEq.keys():
            if key in self.updatedTexs_m2to:
                self.updatedIds[self.missingTexsEq[key]] = self.updatedTexs_m2to[key]

        for t, texture in enumerate(self.texs):
            if int.from_bytes(texture, 'little') in self.updatedIds:
                self.texs[t] = self.updatedIds[int.from_bytes(texture, 'little')].to_bytes(2, 'little')
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
            for i in range(self.nPrtclsM2From):
                for i2, _ in enumerate(self.PRTCL_IDXS):
                    Binary.write_bytes(model_m2to, self.prtclsAddrM2To + M2Length.prtcl * i + self.PRTCL_IDXS[i2], self.DATA_m2from[i2][i])

        with open(self.m2To, "rb+") as model_m2to:
            for i in range(self.nPrtclsM2From):
                for i2, _ in enumerate(offsetToTsPairs_m2to[i]):
                    if i2 in (10, 11, 12, 13, 14):
                        # Вставляем nValues и ofsValues в Timestamps
                        final_offset1 = model_m2to.seek(0, 2)
                        Binary.write_bytes(model_m2to, final_offset1, bytes(*Ts_Final_Ts_bytes[i][i2]))
                        Binary.write_bytes(model_m2to, int(*offsetToTsPairs_m2to[i][i2]), bytes(*Ts_Val_bytes[i][i2]))
                        # Вставляем nValues и ofsValues в Values
                        final_offset2 = model_m2to.seek(0, 2)
                        Binary.write_bytes(model_m2to, final_offset2, bytes(*Val_Final_Val_bytes[i][i2]))
                        Binary.write_bytes(model_m2to, int(*offsetToKfPairs_m2to[i][i2]), bytes(*Val_Val_bytes[i][i2]))
                    else:
                        # Вставляем nValues и ofsValues в Timestamps
                        final_offset1 = model_m2to.seek(0, 2)
                        Binary.write_bytes(model_m2to, final_offset1, bytes(*Ts_Final_Ts_bytes[i][i2]))
                        Binary.write_bytes(model_m2to, int(*offsetToTsPairs_m2to[i][i2]), bytes(*Ts_Val_bytes[i][i2]))
                        Binary.write_bytes(model_m2to, int(*offsetToTsPairs_m2to[i][i2]) + 4, final_offset1.to_bytes(4, 'little'))
                        # Вставляем nValues и ofsValues в Values
                        final_offset2 = model_m2to.seek(0, 2)
                        Binary.write_bytes(model_m2to, final_offset2, bytes(*Val_Final_Val_bytes[i][i2]))
                        Binary.write_bytes(model_m2to, int(*offsetToKfPairs_m2to[i][i2]), bytes(*Val_Val_bytes[i][i2]))
                        Binary.write_bytes(model_m2to, int(*offsetToKfPairs_m2to[i][i2]) + 4, final_offset2.to_bytes(4, 'little'))

        if self.identifyBones:  # * обновляем позиции частиц ------------------------------------------------------------------------------
            self.update_particle_pos()
        # * Выводим сообщение об успешном копировании -------------------------------------------------------------------------------------
        if enabledin_skipped:
            StatusBar.success_info(str(self.nPrtclsM2From) + " particles copied successfully. Total " + str(
                self.nPrtclsM2From + self.nPrtclsM2To) + " particles in model. 'Enabledin' block not copied because there are "
                                                         "no same animation ID in models.")
        else:
            StatusBar.success_info(str(self.nPrtclsM2From) + " particles copied successfully. Total " + str(
                self.nPrtclsM2From + self.nPrtclsM2To) + " particles in model.")

    def enabledin(self):
        def ts_ratio(ts_id_: int, ts_m2From_: bytes, Anims_id_and_len_m2From_: dict, Anims_id_and_len_m2To_Modified_: dict) -> bytes:
            ts_len = len(ts_m2From_)
            _Anims_id_and_length_m2From = list(Anims_id_and_len_m2From_.values())
            Anims_id_and_length_m2To_Modified_LIST = list(Anims_id_and_len_m2To_Modified_.values())
            full_ts_bytes = b''

            for anim_id_ in _Anims_id_and_length_m2From:
                if ts_id_ == anim_id_[0]:
                    sub_index_1 = _Anims_id_and_length_m2From.index(anim_id_)
                    sub_index_2 = anim_id_.index(anim_id_[1])
                    anim_length_m2From = _Anims_id_and_length_m2From[sub_index_1][sub_index_2]
                    anim_length_m2To = Anims_id_and_length_m2To_Modified_LIST[sub_index_1][sub_index_2]
                    Ts_MAX = max(anim_length_m2From, anim_length_m2To)
                    Ts_MIN = min(anim_length_m2From, anim_length_m2To)
                    if Ts_MAX == anim_length_m2From:
                        ratio = Ts_MIN / Ts_MAX
                    elif Ts_MAX == anim_length_m2To:
                        ratio = Ts_MAX / Ts_MIN
                    for step in range(0, ts_len, 4):
                        sliced_timestamp = round(int.from_bytes(ts_m2From_[step:step + 4], 'little') * ratio)
                        full_ts_bytes += sliced_timestamp.to_bytes(4, 'little')

            return full_ts_bytes

        def writing_ts_and_val_modelTo(model_m2to_: BinaryIO, i_: int, pos1: int, pos2: int):
            Binary.write_bytes(model_m2to_, self.prtclsAddrM2To + M2Length.prtcl * i_ + pos1, self.nAnimsM2To_bytes)
            enabledin_last_offset = Binary.write_to_end(model_m2to_, b'\x00' * 8 * self.nAnimsM2To)
            Binary.write_bytes(model_m2to_, self.prtclsAddrM2To + M2Length.prtcl * i_ + pos2,
                               enabledin_last_offset.to_bytes(4, byteorder='little'))

        def writing_one_zero_m2To(model_m2to_: BinaryIO, enum_: int, pos: int, n_: int):
            last_Ts_Offset_ = Binary.write_to_end(model_m2to_, b'\x00' * 4)
            ts_offset = Binary.get_int_from_bytes(model_m2to_, self.prtclsAddrM2To + M2Length.prtcl * enum_ + pos)
            Binary.write_bytes(model_m2to_, ts_offset + 8 * n_, b'\x01\x00\x00\x00')
            Binary.write_bytes(model_m2to_, ts_offset + 8 * n_ + 4, last_Ts_Offset_.to_bytes(4, byteorder='little'))

        # Определяем число анимаций и их адрес в m2From -----------------------------------------------------------------------------------
        with open(self.m2From, 'rb') as model_m2from:
            self.nAnimsM2From = Binary.get_int_from_bytes(model_m2from, M2Offset.nAnim)
            self.animsAddrM2From = Binary.get_int_from_bytes(model_m2from, M2Offset.ofsAnims)

        # Создаем необходимые списки
        if self.nAnimsM2From == 1:
            enabledin_Ts_Offsets = []
            enabledin_Ts_Val = []
            enabledin_Val_Offsets = []
            enabledin_Val_Val = []
        else:
            enabledin_Ts_Offsets = [[] for _ in range(self.nAnimsM2From)]
            enabledin_Ts_Val = [[] for _ in range(self.nAnimsM2From)]
            enabledin_Val_Offsets = [[] for _ in range(self.nAnimsM2From)]
            enabledin_Val_Val = [[] for _ in range(self.nAnimsM2From)]

        enabledin_Ts_Kf = []
        Anims_id_with_val = []
        Anims_id_and_length_m2From = {}
        All_Anims_id_and_length_m2To = {}
        Anims_id_and_length_m2To_Modified = {}
        Ts_Offset_and_n_m2From = [[] for _ in range(self.nPrtclsM2From)]
        Val_Offset_and_n_m2From = [[] for _ in range(self.nPrtclsM2From)]
        Ts_Val_m2From = [[] for _ in range(self.nPrtclsM2From)]
        Val_Val_m2From = [[] for _ in range(self.nPrtclsM2From)]

        # * Проходим по блокам enabledin
        with open(self.m2From, "rb") as model_m2from:
            for i in range(self.nPrtclsM2From):
                enabledin_numbOfTsPairs, enabledin_numbOfTsPairs_bytes = Binary.get_int_and_bytes(model_m2from, self.prtclsAddrM2From +
                                                                                                  M2Length.prtcl * i + 460)
                # Если блок enabledin не пустой и больше 1, добавляем число кейфреймов в соответствующий id частицы
                if enabledin_numbOfTsPairs_bytes > b'\x01\x00\x00\x00':
                    enabledin_Ts_Kf.append(enabledin_numbOfTsPairs)
                    # Берем значения timestamps и keyframes офсетов и добавляем их в списки
                    offsetToTsPairs = Binary.get_int_from_bytes(model_m2from, self.prtclsAddrM2From + M2Length.prtcl * i + 464)
                    offsetToKfPairs = Binary.get_int_from_bytes(model_m2from, self.prtclsAddrM2From + M2Length.prtcl * i + 472)
                    sub_Index = 0
                    for n_seq in range(enabledin_numbOfTsPairs):
                        # Собираем timestamps
                        ts_seq_values = Binary.get_int_from_bytes(model_m2from, offsetToTsPairs + 8 * n_seq)
                        enabledin_Ts_Val[i].append(ts_seq_values)

                        ts_seq_offset = Binary.get_int_from_bytes(model_m2from, offsetToTsPairs + 4 + 8 * n_seq)
                        enabledin_Ts_Offsets[i].append(ts_seq_offset)
                        # Собираем keyframes
                        val_seq_val = Binary.get_int_from_bytes(model_m2from, offsetToKfPairs + 8 * n_seq)
                        enabledin_Val_Val[i].append(val_seq_val)

                        val_seq_offset = Binary.get_int_from_bytes(model_m2from, offsetToKfPairs + 4 + 8 * n_seq)
                        enabledin_Val_Offsets[i].append(val_seq_offset)

                        val_bytes = Binary.read_bytes(model_m2from, val_seq_offset, length=2)
                        # При условии, что n значений >1 или само значение отлично от 0 добавляем id этих анимаций в словари
                        if val_seq_val > 1 or int.from_bytes(val_bytes, 'little') == 1:
                            Ts_Offset_and_n_m2From[i].append([])
                            Val_Offset_and_n_m2From[i].append([])
                            Anims_id_with_val.append(n_seq)
                            Ts_Offset_and_n_m2From[i][sub_Index].append(n_seq)
                            Ts_Offset_and_n_m2From[i][sub_Index].append(ts_seq_offset)
                            Ts_Offset_and_n_m2From[i][sub_Index].append(val_seq_val)
                            Val_Offset_and_n_m2From[i][sub_Index].append(n_seq)
                            Val_Offset_and_n_m2From[i][sub_Index].append(val_seq_offset)
                            Val_Offset_and_n_m2From[i][sub_Index].append(val_seq_val)
                            sub_Index += 1
                # Если блок enabledin не пустой (всего 1 анимация) например оружие, щиты
                elif enabledin_numbOfTsPairs_bytes == b'\x01\x00\x00\x00':
                    enabledin_Ts_Kf.append(enabledin_numbOfTsPairs)
                    # Берем значения timestamps и keyframes офсетов и добавляем их в списки
                    offsetToTsPairs = Binary.get_int_from_bytes(model_m2from, self.prtclsAddrM2From + M2Length.prtcl * i + 464)
                    offsetToKfPairs = Binary.get_int_from_bytes(model_m2from, self.prtclsAddrM2From + M2Length.prtcl * i + 472)
                    sub_Index = 0
                    for n_seq in range(enabledin_numbOfTsPairs):
                        # Собираем timestamps
                        ts_seq_values = Binary.get_int_from_bytes(model_m2from, offsetToTsPairs + 8 * n_seq)
                        enabledin_Ts_Val.append(ts_seq_values)

                        ts_seq_offset = Binary.get_int_from_bytes(model_m2from, offsetToTsPairs + 4 + 8 * n_seq)
                        enabledin_Ts_Offsets.append(ts_seq_offset)
                        # Собираем keyframes
                        val_seq_val = Binary.get_int_from_bytes(model_m2from, offsetToKfPairs + 8 * n_seq)
                        enabledin_Val_Val.append(val_seq_val)

                        val_seq_offset = Binary.get_int_from_bytes(model_m2from, offsetToKfPairs + 4 + 8 * n_seq)
                        enabledin_Val_Offsets.append(val_seq_offset)

                        val_bytes = Binary.read_bytes(model_m2from, val_seq_offset, length=2)
                        # При условии, что n значений >1 или само значение отлично от 0 добавляем id этих анимаций в словари
                        if val_seq_val > 1 or int.from_bytes(val_bytes, 'little') == 1:
                            Ts_Offset_and_n_m2From[i].append([])
                            Val_Offset_and_n_m2From[i].append([])
                            Anims_id_with_val.append(n_seq)
                            Ts_Offset_and_n_m2From[i][sub_Index].append(n_seq)
                            Ts_Offset_and_n_m2From[i][sub_Index].append(ts_seq_offset)
                            Ts_Offset_and_n_m2From[i][sub_Index].append(val_seq_val)
                            Val_Offset_and_n_m2From[i][sub_Index].append(n_seq)
                            Val_Offset_and_n_m2From[i][sub_Index].append(val_seq_offset)
                            Val_Offset_and_n_m2From[i][sub_Index].append(val_seq_val)
                            sub_Index += 1
                # Если пустой, то 0
                else:
                    enabledin_Ts_Kf.append(0)

        # * Создаем множество, чтобы оставить только уникальные id анимаций
        Anims_id_with_val_Unique = sorted(set(Anims_id_with_val))

        # И проходимся по ним и добавляем в словарь
        with open(self.m2From, "rb") as model_m2from:
            for anim in Anims_id_with_val_Unique:
                SubAnimID = str(Binary.get_int_from_bytes(model_m2from, self.animsAddrM2From + M2Length.anim * anim + 2, length=2))
                anim_id = str(Binary.get_int_from_bytes(model_m2from, self.animsAddrM2From + M2Length.anim * anim,
                                                        length=2)) + "_" + SubAnimID
                anim_length = Binary.get_int_from_bytes(model_m2from, self.animsAddrM2From + M2Length.anim * anim + 4)

                Anims_id_and_length_m2From[anim_id] = anim, anim_length

        # * Определяем количество анимаций и их адреса в целевой модели
        with open(self.m2To, "rb") as model_m2to:
            self.nAnimsM2To, self.nAnimsM2To_bytes = Binary.get_int_and_bytes(model_m2to, M2Offset.nAnim)
            self.animsAddrM2To = Binary.get_int_from_bytes(model_m2to, M2Offset.ofsAnims)
            for anim in range(self.nAnimsM2To):
                SubAnimID = str(Binary.get_int_from_bytes(model_m2to, self.animsAddrM2To + M2Length.anim * anim + 2, length=2))
                anim_id = str(Binary.get_int_from_bytes(model_m2to, self.animsAddrM2To + M2Length.anim * anim,
                                                        length=2)) + "_" + SubAnimID
                anim_length = Binary.get_int_from_bytes(model_m2to, self.animsAddrM2To + M2Length.anim * anim + 4)

                All_Anims_id_and_length_m2To[anim_id] = anim, anim_length

        # * Проверяем соответствие id анимаций в обеих моделях
        anims_id_link = {}
        for key in Anims_id_and_length_m2From:
            if key in All_Anims_id_and_length_m2To:
                anims_id_link[Anims_id_and_length_m2From[key][0]] = All_Anims_id_and_length_m2To[key][0]
                Anims_id_and_length_m2To_Modified[key] = All_Anims_id_and_length_m2To[key]

        # Копируем значения Timestamps
        with open(self.m2From, "rb") as model_m2from:
            for i, ts in enumerate(Ts_Offset_and_n_m2From):
                if ts:
                    for i2, ts2 in enumerate(ts):
                        ts_id = ts2[0]
                        Ts_Val_m2From[i].append([])
                        ts_m2From = Binary.read_bytes(model_m2from, ts2[1], length=ts2[2] * 4)
                        ts_from_function = ts_ratio(ts_id, ts_m2From, Anims_id_and_length_m2From, Anims_id_and_length_m2To_Modified)
                        Ts_Val_m2From[i][i2].append(ts2[0])
                        Ts_Val_m2From[i][i2].append(ts_from_function)

        # Копируем значения Values
        with open(self.m2From, "rb") as model_m2from:
            for i, Val in enumerate(Val_Offset_and_n_m2From):
                if Val:
                    for i2, Val2 in enumerate(Val):
                        Val_Val_m2From[i].append([])
                        Val_modelFrom = Binary.read_bytes(model_m2from, Val2[1], length=Val2[2])
                        Val_Val_m2From[i][i2].append(Val2[0])
                        Val_Val_m2From[i][i2].append(Val_modelFrom)

        # Прописываем Timestamps и Values в целевой модели
        with open(self.m2To, "rb+") as model_m2to:
            for i, kf in enumerate(enabledin_Ts_Kf):
                if kf != 0:
                    writing_ts_and_val_modelTo(model_m2to, i, 460, 464)  # Timestamps
                    writing_ts_and_val_modelTo(model_m2to, i, 468, 472)  # Values

        # Прописываем во все Timestamp->Sequence 1 и 0 и Values->Sequence 1 и 0 в целевой модели
        with open(self.m2To, "rb+") as model_m2to:
            for enum, i in enumerate(enabledin_Ts_Kf):
                if i != 0:
                    for n in range(self.nAnimsM2To):
                        writing_one_zero_m2To(model_m2to, enum, 464, n)  # Timestamps
                        writing_one_zero_m2To(model_m2to, enum, 472, n)  # Values

        # Вставляем в имеющиеся id значения Timestamps из списка
        with open(self.m2To, "rb+") as model_m2to:
            for i in range(len(enabledin_Ts_Kf)):
                for n in range(self.nAnimsM2To):
                    for ts_array in Ts_Offset_and_n_m2From[i]:
                        for val in Ts_Val_m2From[i]:
                            if ts_array[0] in anims_id_link and anims_id_link[ts_array[0]] == n and ts_array[0] == val[0]:
                                last_Ts_Offset = Binary.write_to_end(model_m2to, val[1])

                                ts_offset1 = Binary.get_int_from_bytes(model_m2to, self.prtclsAddrM2To + M2Length.prtcl * i + 464)
                                Binary.write_bytes(model_m2to, ts_offset1 + 8 * n, ts_array[2].to_bytes(4, byteorder='little'))
                                Binary.write_bytes(model_m2to, ts_offset1 + 8 * n + 4, last_Ts_Offset.to_bytes(4, byteorder='little'))

        # Вставляем в имеющиеся id значения Values из списка
        with open(self.m2To, "rb+") as model_m2to:
            for i in range(len(enabledin_Ts_Kf)):
                for n in range(self.nAnimsM2To):
                    for val_array in Val_Offset_and_n_m2From[i]:
                        for val2 in Val_Val_m2From[i]:
                            if val_array[0] in anims_id_link and anims_id_link[val_array[0]] == n and val_array[0] == val2[0]:
                                last_Ts_Offset3 = Binary.write_to_end(model_m2to, val2[1])

                                ts_offset4 = Binary.get_int_from_bytes(model_m2to, self.prtclsAddrM2To + M2Length.prtcl * i + 472)
                                Binary.write_bytes(model_m2to, ts_offset4 + 8 * n, val_array[2].to_bytes(4, byteorder='little'))
                                Binary.write_bytes(model_m2to, ts_offset4 + 8 * n + 4, last_Ts_Offset3.to_bytes(4, byteorder='little'))

    def identify_bones(self):
        with open(self.m2From, "rb+") as model_m2from:
            self.nBonesM2From = Binary.get_int_from_bytes(model_m2from, M2Offset.nBones)
            self.bonesAddrM2From = Binary.get_int_from_bytes(model_m2from, M2Offset.ofsBones)

            for i in range(self.nBonesM2From):
                kb_id_m2from = Binary.get_int_from_bytes(model_m2from, self.bonesAddrM2From + i * M2Length.bone)
                if kb_id_m2from != 4294967295:  # 4294967295 = KBNone(-1)
                    self.keyBoneIdsM2From.append(kb_id_m2from)

        with open(self.m2To, "rb+") as model_m2to:
            self.nBonesM2To = Binary.get_int_from_bytes(model_m2to, M2Offset.nBones)
            self.bonesAddrM2To = Binary.get_int_from_bytes(model_m2to, M2Offset.ofsBones)

            for i in range(self.nBonesM2To):
                kb_id_m2to = Binary.get_int_from_bytes(model_m2to, self.bonesAddrM2To + i * M2Length.bone)
                if kb_id_m2to != 4294967295:
                    self.keyBoneIdsM2To[kb_id_m2to] = i

    def get_key_bone_id(self, model_: BinaryIO, parent_bone_: int) -> int:
        k_b_id = Binary.get_int_from_bytes(model_, self.bonesAddrM2From + M2Length.bone * parent_bone_)
        if k_b_id == 4294967295:
            new_parent_bone = Binary.get_int_from_bytes(model_, self.bonesAddrM2From + M2Length.bone * parent_bone_ + 8, length=2)
            if new_parent_bone != 65535:  # 65535 = -1
                new_parent_bone = self.get_key_bone_id(model_, new_parent_bone)
            return new_parent_bone
        return k_b_id

    def update_particle_pos(self):
        with open(self.m2To, "rb+") as model_m2to:
            for i, bone_id in enumerate(self.isNeedToUpdateParticlePos):
                if bone_id:
                    new_pos = Binary.read_bytes(model_m2to, self.bonesAddrM2To + M2Length.bone * bone_id + M2Offset.pivotPnt,
                                                length=M2Length.pivotPnt)
                    Binary.write_bytes(model_m2to, self.prtclsAddrM2To + M2Length.prtcl * i + 8, new_pos)

    def copy_missing_textures_to_patch_folder(self, missing_tex_: bytes):
        tex_path_ = missing_tex_.decode("utf-8").strip("\x00")
        src_path_ = os.path.join(os.path.dirname(self.m2From), os.path.basename(tex_path_))
        dest_path_ = os.path.join(reg_manager.patchFolder, tex_path_)
        dest_folder = os.path.dirname(dest_path_)
        if not os.path.exists(dest_path_) and os.path.exists(src_path_):
            if not os.path.exists(dest_folder):
                os.mkdir(dest_folder)
            try:
                shutil.copy2(src_path_, dest_path_)
            except OSError:
                pass


def particle_cloner_init():
    StatusBar.clear_info()
    particle_cloner = ParticleCloner()
    particle_cloner.copy_particles_pre()
