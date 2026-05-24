import dearpygui.dearpygui as dpg

from utils.binary import Binary
from utils.miscellaneous import check_model_path
from utils.offsets import M2Offsets, M2Lengths
from utils.statusbar import StatusBar


def create_nTextureCombiner_pre():
    StatusBar.clear_info()

    model_path = check_model_path()
    if model_path is None:
        return

    add_n_textureCombiner = dpg.get_value("inp_nTextureCombiner")
    if add_n_textureCombiner == "":
        StatusBar.error_info("ERROR: Enter the n TextureCombiner.")
        return
    else:
        add_n_textureCombiner = int(add_n_textureCombiner)

    create_nTextureCombiner(model_path, add_n_textureCombiner)


def create_nTextureCombiner(model_path: str, add_n_textureCombiner: int):
    if add_n_textureCombiner % 2 != 0:
        add_n_textureCombiner += 1

    with open(model_path, 'rb+') as model:
        md_structure = model.read(4)
        if md_structure != b'\x4D\x44\x32\x30':
            StatusBar.error_info("ERROR: Сonvert the model before editing")
            return

        # Проверяем включен ли GlobalFlag
        flag = Binary.read_bytes(model, M2Offsets.globalFlags, length=1)

        if str(flag)[5:-1] in ("8", "9", "A", "B", "C", "D", "E", "F", "nBones", "b", "c", "d", "e", "f"):
            nTextureCombiner = Binary.get_int_from_bytes(model, M2Offsets.nTextureCombiner)
            ofsTextureCombiner = Binary.get_int_from_bytes(model, M2Offsets.ofsTextureCombiner)
            existingTextureCombiner = Binary.read_bytes(model, ofsTextureCombiner, length=nTextureCombiner * 2)

            new_ofsTextureCombiner = Binary.write_offset(model)
            model.write(existingTextureCombiner + b'\x01\x00' * add_n_textureCombiner)

            Binary.write_bytes(model, M2Offsets.nTextureCombiner, (nTextureCombiner + add_n_textureCombiner).to_bytes(4, 'little'))
            Binary.write_bytes(model, M2Offsets.ofsTextureCombiner, new_ofsTextureCombiner[0].to_bytes(4, 'little'))
        else:
            nTextureCombiner = 0
            # Проверяем есть ли sequences и они находятся по адресу 130h если да то переносим их
            nGlobSeq = Binary.get_int_from_bytes(model, M2Offsets.nGlobalSequences)

            if nGlobSeq > 0:
                ofsGlobSeq = Binary.get_int_from_bytes(model, M2Offsets.ofsGlobalSequences)

                if ofsGlobSeq == M2Offsets.nTextureCombiner:
                    existingGlobSeq = Binary.read_bytes(model, ofsGlobSeq, length=nGlobSeq * 4)

                    Binary.write_zeros(model)

                    new_ofsGlobSeq = model.seek(0, 2)
                    # Добавляем запас на всякий случай 8шт
                    model.write(existingGlobSeq + b'\x00\x00\x00\x00' * 8)

                    Binary.write_zeros(model)

                    Binary.write_bytes(model, M2Offsets.ofsGlobalSequences, new_ofsGlobSeq.to_bytes(4, 'little'))

            # Добавляем флаг TextureCombiner
            Binary.write_bytes(model, M2Offsets.globalFlags, b'\x98')

            new_ofsTextureCombiner = model.seek(0, 2)
            model.write(b'\x01\x00' * add_n_textureCombiner)

            Binary.write_bytes(model, M2Offsets.nTextureCombiner, add_n_textureCombiner.to_bytes(4, 'little'))
            Binary.write_bytes(model, M2Offsets.ofsTextureCombiner, new_ofsTextureCombiner.to_bytes(4, 'little'))

        Binary.write_zeros(model)

        StatusBar.success_info(f"{add_n_textureCombiner} TextureCombiner created. "
                               f"Total {nTextureCombiner + add_n_textureCombiner} TextureCombiner in model.")


def create_nGlobalSeq_pre():
    StatusBar.clear_info()

    model_path = check_model_path()
    if model_path is None:
        return

    add_n_globalSeq = dpg.get_value("inp_nGlobalSeq")
    if add_n_globalSeq == "":
        StatusBar.error_info("ERROR: Enter the n GlobalSeq.")
        return
    else:
        add_n_globalSeq = int(add_n_globalSeq)

    create_nGlobalSeq(model_path, add_n_globalSeq)


def create_nGlobalSeq(model_path: str, add_n_globalSeq: int):
    with open(model_path, 'rb+') as model:
        MD_structure = model.read(4)

        if MD_structure != b'\x4D\x44\x32\x30':
            StatusBar.error_info("ERROR: Сonvert the model before editing")
            return

        nGlobalSeq = Binary.get_int_from_bytes(model, M2Offsets.nGlobalSequences)
        ofsGlobalSeq = Binary.get_int_from_bytes(model, M2Offsets.ofsGlobalSequences)

        if nGlobalSeq > 0:
            existingGlobalSeq = Binary.read_bytes(model, ofsGlobalSeq, length=nGlobalSeq * 4)
        else:
            existingGlobalSeq = b''

        Binary.write_zeros(model)

        new_ofsGlobalSeq = model.seek(0, 2)
        model.write(existingGlobalSeq + b'\x00\x00\x00\x00' * add_n_globalSeq)

        Binary.write_bytes(model, M2Offsets.nGlobalSequences, (nGlobalSeq + add_n_globalSeq).to_bytes(4, 'little'))
        Binary.write_bytes(model, M2Offsets.ofsGlobalSequences, new_ofsGlobalSeq.to_bytes(4, 'little'))

        Binary.write_zeros(model)

    StatusBar.success_info(f"{add_n_globalSeq} GlobalSeq created. Total {nGlobalSeq + add_n_globalSeq} GlobalSeq in model.")


def create_nBones_pre():
    StatusBar.clear_info()

    model_path = check_model_path()
    if model_path is None:
        return

    add_n_bones = dpg.get_value("inp_nBones")
    if add_n_bones == "":
        StatusBar.error_info("ERROR: Enter the n Bones.")
        return
    else:
        add_n_bones = int(add_n_bones)

    add_n_keyframe = dpg.get_value("inp_nBones_keyframes")
    if add_n_keyframe == "":
        add_n_keyframe = 1
    else:
        add_n_keyframe = int(add_n_keyframe)

    create_nBones(model_path, add_n_bones, add_n_keyframe)


def create_nBones(model_path: str, add_n_bones: int, add_n_keyframe: int):
    add_n_keyframe_bytes = add_n_keyframe.to_bytes(4, byteorder='little')
    OFFSETS_Bones_Translation = (20, 24, 28, 32)
    OFFSETS_Bones_Rotation = (40, 44, 48, 52)
    OFFSETS_Bones_Scale = (60, 64, 68, 72)
    seq_offsets_Bones_Translation = []
    seq_offsets_Bones_Rotation = []
    seq_offsets_Bones_Scale = []

    with open(model_path, 'rb+') as model:
        MD_structure = model.read(4)
        if MD_structure != b'\x4D\x44\x32\x30':
            StatusBar.error_info("ERROR: Сonvert the model before editing")
            return

        nBones = Binary.get_int_from_bytes(model, M2Offsets.nBones)
        ofsBones = Binary.get_int_from_bytes(model, M2Offsets.ofsBones)

        if nBones > 0:
            existingBones = Binary.read_bytes(model, ofsBones, length=nBones * M2Lengths.bone)
        else:
            existingBones = b''

        Binary.write_zeros(model)

        # Вставляем имеющиеся Bones
        new_ofsBones = model.seek(0, 2)
        model.write(existingBones + b'\xFF\xFF\xFF\xFF\x00\x02\x00\x00\xFF\xFF\x00\x00\xC7\x6B\x9F\x06'
                                    b'\x01\x00\xFF\xFF\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                                    b'\x00\x00\x00\x00\x01\x00\xFF\xFF\x00\x00\x00\x00\x00\x00\x00\x00'
                                    b'\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\xFF\xFF\x00\x00\x00\x00'
                                    b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80'
                                    b'\x00\x00\x00\x00\x00\x00\x00\x00' * add_n_bones)

        # Переназначаем офсет и число Bones
        Binary.write_bytes(model, M2Offsets.nBones, (nBones + add_n_bones).to_bytes(4, 'little'))
        Binary.write_bytes(model, M2Offsets.ofsBones, new_ofsBones.to_bytes(4, 'little'))

        # Прописываем keyframes для Timestamps и Values
        for i in range(nBones, nBones + add_n_bones):
            if dpg.get_value("chk_Bones_Translation"):
                for offset in OFFSETS_Bones_Translation:
                    if (OFFSETS_Bones_Translation.index(offset) + 1) % 2 == 1:
                        Binary.write_bytes(model, new_ofsBones + M2Lengths.bone * i + offset, b'\x01\x00\x00\x00')
                    if (OFFSETS_Bones_Translation.index(offset) + 1) % 2 == 0:
                        last_offset = Binary.write_offset(model)
                        seq_offsets_Bones_Translation.append(last_offset[0])
                        Binary.write_bytes(model, new_ofsBones + M2Lengths.bone * i + offset, last_offset[1])

            if dpg.get_value("chk_Bones_Rotation"):
                for offset in OFFSETS_Bones_Rotation:
                    if (OFFSETS_Bones_Rotation.index(offset) + 1) % 2 == 1:
                        Binary.write_bytes(model, new_ofsBones + M2Lengths.bone * i + offset, b'\x01\x00\x00\x00')
                    if (OFFSETS_Bones_Rotation.index(offset) + 1) % 2 == 0:
                        last_offset = Binary.write_offset(model)
                        seq_offsets_Bones_Rotation.append(last_offset[0])
                        Binary.write_bytes(model, new_ofsBones + M2Lengths.bone * i + offset, last_offset[1])

            if dpg.get_value("chk_Bones_Scale"):
                for offset in OFFSETS_Bones_Scale:
                    if (OFFSETS_Bones_Scale.index(offset) + 1) % 2 == 1:
                        Binary.write_bytes(model, new_ofsBones + M2Lengths.bone * i + offset, b'\x01\x00\x00\x00')
                    if (OFFSETS_Bones_Scale.index(offset) + 1) % 2 == 0:
                        last_offset = Binary.write_offset(model)
                        seq_offsets_Bones_Scale.append(last_offset[0])
                        Binary.write_bytes(model, new_ofsBones + M2Lengths.bone * i + offset, last_offset[1])

        if dpg.get_value("chk_Bones_Translation"):
            for seq_offset in seq_offsets_Bones_Translation:
                if (seq_offsets_Bones_Translation.index(seq_offset) + 1) % 2 == 1:
                    last_offset = Binary.write_seq_offset(model, add_n_keyframe)
                else:
                    last_offset = Binary.write_seq_offset(model, add_n_keyframe, value_bytes=b'\x00\x00\x00\x00' * 3)

                Binary.write_bytes(model, seq_offset, add_n_keyframe_bytes)
                Binary.write_bytes(model, seq_offset + 4, last_offset)

        if dpg.get_value("chk_Bones_Rotation"):
            for seq_offset in seq_offsets_Bones_Rotation:
                if (seq_offsets_Bones_Rotation.index(seq_offset) + 1) % 2 == 1:
                    last_offset = Binary.write_seq_offset(model, add_n_keyframe)
                else:
                    last_offset = Binary.write_seq_offset(model, add_n_keyframe, value_bytes=b'\xFF\x7F' * 4)

                Binary.write_bytes(model, seq_offset, add_n_keyframe_bytes)
                Binary.write_bytes(model, seq_offset + 4, last_offset)

        if dpg.get_value("chk_Bones_Scale"):
            for seq_offset in seq_offsets_Bones_Scale:
                if (seq_offsets_Bones_Scale.index(seq_offset) + 1) % 2 == 1:
                    last_offset = Binary.write_seq_offset(model, add_n_keyframe)
                else:
                    last_offset = Binary.write_seq_offset(model, add_n_keyframe, value_bytes=b'\x00\x00\x80\x3F' * 3)

                Binary.write_bytes(model, seq_offset, add_n_keyframe_bytes)
                Binary.write_bytes(model, seq_offset + 4, last_offset)

        Binary.write_zeros(model)

    # Добавляем пункты в BoneLookupTable
    update_nBoneLookupTable(model_path, add_n_bones)

    StatusBar.success_info(f"{add_n_bones} Bones created. Total {nBones + add_n_bones} Bones in model.")


def create_nColor_pre():
    StatusBar.clear_info()

    model_path = check_model_path()
    if model_path is None:
        return

    add_n_color = dpg.get_value("inp_nColor")
    if add_n_color == "":
        StatusBar.error_info("ERROR: Enter the n Color.")
        return
    else:
        add_n_color = int(add_n_color)

    add_n_keyframe = dpg.get_value("inp_nColor_keyframes")
    if add_n_keyframe == "":
        add_n_keyframe = 1
    else:
        add_n_keyframe = int(add_n_keyframe)

    create_nColor(model_path, add_n_color, add_n_keyframe)


def create_nColor(model_path: str, add_n_color: int, add_n_keyframe: int):
    add_n_keyframe_bytes = add_n_keyframe.to_bytes(4, byteorder='little')
    OFFSETS_Color = (4, 8, 12, 16, 24, 28, 32, 36)
    seq_offsets_Color = []

    with open(model_path, 'rb+') as model:
        MD_structure = model.read(4)
        if MD_structure != b'\x4D\x44\x32\x30':
            StatusBar.error_info("ERROR: Сonvert the model before editing")
            return

        nColor = Binary.get_int_from_bytes(model, M2Offsets.nColors)
        ofsColor = Binary.get_int_from_bytes(model, M2Offsets.ofsColors)

        if nColor > 0:
            existingColor = Binary.read_bytes(model, ofsColor, length=nColor * M2Lengths.color)
        else:
            existingColor = b''

        Binary.write_zeros(model)

        new_ofsColor = model.seek(0, 2)
        model.write(existingColor + b'\x01\x00\xff\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' * 2 * add_n_color)

        # Переназначаем офсет и число Color
        Binary.write_bytes(model, M2Offsets.nColors, (nColor + add_n_color).to_bytes(4, 'little'))
        Binary.write_bytes(model, M2Offsets.ofsColors, new_ofsColor.to_bytes(4, 'little'))

        # Прописываем keyframes для Color и Alpha
        for i in range(nColor, nColor + add_n_color):
            for offset in OFFSETS_Color:
                if (OFFSETS_Color.index(offset) + 1) % 2 == 1:
                    Binary.write_bytes(model, new_ofsColor + M2Lengths.color * i + offset, b'\x01\x00\x00\x00')
                if (OFFSETS_Color.index(offset) + 1) % 2 == 0:
                    last_offset = Binary.write_offset(model)
                    seq_offsets_Color.append(last_offset[0])
                    Binary.write_bytes(model, new_ofsColor + M2Lengths.color * i + offset, last_offset[1])

        every_2_list = [x for x in range(2, len(seq_offsets_Color) + 1, 4)]
        every_4_list = [y for y in range(4, len(seq_offsets_Color) + 1, 4)]

        for seq_offset in seq_offsets_Color:
            if seq_offsets_Color.index(seq_offset) + 1 in every_2_list:
                last_offset = Binary.write_seq_offset(model, add_n_keyframe,
                                                      value_bytes=b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
            elif seq_offsets_Color.index(seq_offset) + 1 in every_4_list:
                last_offset = Binary.write_seq_offset(model, add_n_keyframe, value_bytes=b'\xFF\x7F')
            else:
                last_offset = Binary.write_seq_offset(model, add_n_keyframe)

            Binary.write_bytes(model, seq_offset, add_n_keyframe_bytes)
            Binary.write_bytes(model, seq_offset + 4, last_offset)

        Binary.write_zeros(model)

    StatusBar.success_info(f"{add_n_color} Color created. Total {nColor + add_n_color} Color in model.")


def create_nTransparency_pre():
    StatusBar.clear_info()

    model_path = check_model_path()
    if model_path is None:
        return

    add_n_transparency = dpg.get_value("inp_nTransparency")
    if add_n_transparency == "":
        StatusBar.error_info("ERROR: Enter the n Transparency.")
        return
    else:
        add_n_transparency = int(add_n_transparency)

    add_n_keyframe = dpg.get_value("inp_nTransparency_keyframes")
    if add_n_keyframe == "":
        add_n_keyframe = 1
    else:
        add_n_keyframe = int(add_n_keyframe)

    create_nTransparency(model_path, add_n_transparency, add_n_keyframe)


def create_nTransparency(model_path: str, add_n_transparency: int, add_n_keyframe: int):
    add_n_keyframe_bytes = add_n_keyframe.to_bytes(4, byteorder='little')
    OFFSETS_Transparency = (4, 8, 12, 16)
    seq_offsets_Transparency = []

    with open(model_path, 'rb+') as model:
        MD_structure = model.read(4)
        if MD_structure != b'\x4D\x44\x32\x30':
            StatusBar.error_info("ERROR: Сonvert the model before editing")
            return

        nTransparency = Binary.get_int_from_bytes(model, M2Offsets.nTransparency)
        ofsTransparency = Binary.get_int_from_bytes(model, M2Offsets.ofsTransparency)

        if nTransparency > 0:
            existingTransparency = Binary.read_bytes(model, ofsTransparency, length=nTransparency * M2Lengths.transparency)
        else:
            existingTransparency = b''

        Binary.write_zeros(model)

        new_ofsTransparency = model.seek(0, 2)
        model.write(
            existingTransparency + b'\x01\x00\xff\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' * add_n_transparency)

        # Переназначаем офсет и число Transparency
        Binary.write_bytes(model, M2Offsets.nTransparency, (nTransparency + add_n_transparency).to_bytes(4, 'little'))
        Binary.write_bytes(model, M2Offsets.ofsTransparency, new_ofsTransparency.to_bytes(4, 'little'))

        # Прописываем keyframes для Transparency
        for i in range(nTransparency, nTransparency + add_n_transparency):
            for offset in OFFSETS_Transparency:
                if (OFFSETS_Transparency.index(offset) + 1) % 2 == 1:
                    Binary.write_bytes(model, new_ofsTransparency + M2Lengths.transparency * i + offset, b'\x01\x00\x00\x00')
                if (OFFSETS_Transparency.index(offset) + 1) % 2 == 0:
                    last_offset = Binary.write_offset(model)
                    seq_offsets_Transparency.append(last_offset[0])
                    Binary.write_bytes(model, new_ofsTransparency + M2Lengths.transparency * i + offset, last_offset[1])

        for seq_offset in seq_offsets_Transparency:
            if (seq_offsets_Transparency.index(seq_offset) + 1) % 2 == 0:
                last_offset = Binary.write_seq_offset(model, add_n_keyframe, value_bytes=b'\x00\x00')
            else:
                last_offset = Binary.write_seq_offset(model, add_n_keyframe)

            Binary.write_bytes(model, seq_offset, add_n_keyframe_bytes)
            Binary.write_bytes(model, seq_offset + 4, last_offset)

        Binary.write_zeros(model)

    # Добавляем пункты в Translookup
    update_nTranslookup(model_path, add_n_transparency)

    StatusBar.success_info(f"{add_n_transparency} Transparency created. Total {nTransparency + add_n_transparency} Transparency in model.")


def create_nTextures_pre():
    StatusBar.clear_info()

    model_path = check_model_path()
    if model_path is None:
        return

    add_n_textures = dpg.get_value("inp_nTextures")
    if add_n_textures == "":
        StatusBar.error_info("ERROR: Enter the n Textures.")
        return
    else:
        add_n_textures = int(add_n_textures)

    create_nTextures(model_path, add_n_textures)


def create_nTextures(model_path: str, add_n_textures: int):
    with open(model_path, 'rb+') as model:
        MD_structure = model.read(4)
        if MD_structure != b'\x4D\x44\x32\x30':
            StatusBar.error_info("ERROR: Сonvert the model before editing")
            return

        nTextures = Binary.get_int_from_bytes(model, M2Offsets.nTextures)
        ofsTextures = Binary.get_int_from_bytes(model, M2Offsets.ofsTextures)

        if nTextures > 0:
            existingTextures = Binary.read_bytes(model, ofsTextures, length=nTextures * M2Lengths.texture)
        else:
            existingTextures = b''

        Binary.write_zeros(model)

        new_ofsTextures = model.seek(0, 2)
        model.write(existingTextures + b'\x00\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' * add_n_textures)

        # Переназначаем офсет и число Textures
        Binary.write_bytes(model, M2Offsets.nTextures, (nTextures + add_n_textures).to_bytes(4, 'little'))
        Binary.write_bytes(model, M2Offsets.ofsTextures, new_ofsTextures.to_bytes(4, 'little'))

        Binary.write_zeros(model)

    # Добавляем пункты в TextLookupTable
    update_nTexLookup(model_path, add_n_textures)

    StatusBar.success_info(f"{add_n_textures} Textures created. Total {nTextures + add_n_textures} Textures in model.")


def create_nMaterials_pre():
    StatusBar.clear_info()

    model_path = check_model_path()
    if model_path is None:
        return

    add_n_materials = dpg.get_value("inp_nMaterials")
    if add_n_materials == "":
        StatusBar.error_info("ERROR: Enter the n Materials.")
        return
    else:
        add_n_materials = int(add_n_materials)

    create_nMaterials(model_path, add_n_materials)


def create_nMaterials(model_path: str, add_n_materials: int):
    with open(model_path, 'rb+') as model:
        MD_structure = model.read(4)
        if MD_structure != b'\x4D\x44\x32\x30':
            StatusBar.error_info("ERROR: Сonvert the model before editing")
            return

        nMaterials = Binary.get_int_from_bytes(model, M2Offsets.nMaterials)
        ofsMaterials = Binary.get_int_from_bytes(model, M2Offsets.ofsMaterials)

        if nMaterials > 0:
            existingMaterial = Binary.read_bytes(model, ofsMaterials, length=nMaterials * M2Lengths.material)
        else:
            existingMaterial = b''

        Binary.write_zeros(model)

        new_ofsMaterials = model.seek(0, 2)
        model.write(existingMaterial + b'\x13\x00\x02\x00' * add_n_materials)

        # Переназначаем офсет и число Materials
        Binary.write_bytes(model, M2Offsets.nMaterials, (nMaterials + add_n_materials).to_bytes(4, 'little'))
        Binary.write_bytes(model, M2Offsets.ofsMaterials, new_ofsMaterials.to_bytes(4, 'little'))

        Binary.write_zeros(model)

    StatusBar.success_info(f"{add_n_materials} Materials created. Total {nMaterials + add_n_materials} Materials in model.")


def create_nTextureAnimation_pre():
    StatusBar.clear_info()

    model_path = check_model_path()
    if model_path is None:
        return

    add_n_texture_animation = dpg.get_value("inp_nTextureAnimation")
    if add_n_texture_animation == "":
        StatusBar.error_info("ERROR: Enter the n TextureAnimation.")
        return
    else:
        add_n_texture_animation = int(add_n_texture_animation)

    add_n_keyframe = dpg.get_value("inp_nTextureAnimation_keyframes")
    if add_n_keyframe == "":
        add_n_keyframe = 1
    else:
        add_n_keyframe = int(add_n_keyframe)

    create_nTextureAnimation(model_path, add_n_texture_animation, add_n_keyframe)


def create_nTextureAnimation(model_path: str, add_n_texture_animation: int, add_n_keyframe: int):
    add_n_keyframe_bytes = add_n_keyframe.to_bytes(4, byteorder='little')
    OFFSETS_TextureAnimation_Translation = (4, 8, 12, 16)
    OFFSETS_TextureAnimation_Rotation = (24, 28, 32, 36)
    OFFSETS_TextureAnimation_Scale = (44, 48, 52, 56)
    seq_offsets_TextureAnimation_Translation = []
    seq_offsets_TextureAnimation_Rotation = []
    seq_offsets_TextureAnimation_Scale = []

    with open(model_path, 'rb+') as model:
        MD_structure = model.read(4)
        if MD_structure != b'\x4D\x44\x32\x30':
            StatusBar.error_info("ERROR: Сonvert the model before editing")
            return

        nTextureAnimation = Binary.get_int_from_bytes(model, M2Offsets.nTextureAnimations)
        ofsTextureAnimation = Binary.get_int_from_bytes(model, M2Offsets.ofsTextureAnimations)

        if nTextureAnimation > 0:
            existingTextureAnimation = Binary.read_bytes(model, ofsTextureAnimation, length=nTextureAnimation * M2Lengths.textureAnimation)
        else:
            existingTextureAnimation = b''

        Binary.write_zeros(model)

        new_ofsTextureAnimation = model.seek(0, 2)
        model.write(existingTextureAnimation + b'\x01\x00\xFF\xFF\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                                               b'\x00\x00\x00\x00' * 3 * add_n_texture_animation)

        # Переназначаем офсет и число TextureAnimation
        Binary.write_bytes(model, M2Offsets.nTextureAnimations, (nTextureAnimation + add_n_texture_animation).to_bytes(4, 'little'))
        Binary.write_bytes(model, M2Offsets.ofsTextureAnimations, new_ofsTextureAnimation.to_bytes(4, 'little'))

        # Прописываем keyframes для Timestamps и Values
        for i in range(nTextureAnimation, nTextureAnimation + add_n_texture_animation):
            if dpg.get_value("chk_TextureAnimation_Translation"):
                for offset in OFFSETS_TextureAnimation_Translation:
                    if (OFFSETS_TextureAnimation_Translation.index(offset) + 1) % 2 == 1:
                        Binary.write_bytes(model, new_ofsTextureAnimation + M2Lengths.textureAnimation * i + offset, b'\x01\x00\x00\x00')
                    if (OFFSETS_TextureAnimation_Translation.index(offset) + 1) % 2 == 0:
                        last_offset = Binary.write_offset(model)
                        seq_offsets_TextureAnimation_Translation.append(last_offset[0])
                        Binary.write_bytes(model, new_ofsTextureAnimation + M2Lengths.textureAnimation * i + offset, last_offset[1])

            if dpg.get_value("chk_TextureAnimation_Rotation"):
                for offset in OFFSETS_TextureAnimation_Rotation:
                    if (OFFSETS_TextureAnimation_Rotation.index(offset) + 1) % 2 == 1:
                        Binary.write_bytes(model, new_ofsTextureAnimation + M2Lengths.textureAnimation * i + offset, b'\x01\x00\x00\x00')
                    if (OFFSETS_TextureAnimation_Rotation.index(offset) + 1) % 2 == 0:
                        last_offset = Binary.write_offset(model)
                        seq_offsets_TextureAnimation_Rotation.append(last_offset[0])
                        Binary.write_bytes(model, new_ofsTextureAnimation + M2Lengths.textureAnimation * i + offset, last_offset[1])

            # В любом случаем для Scale создаем keyframes потом пригодятся
            for offset in OFFSETS_TextureAnimation_Scale:
                if (OFFSETS_TextureAnimation_Scale.index(offset) + 1) % 2 == 1:
                    Binary.write_bytes(model, new_ofsTextureAnimation + M2Lengths.textureAnimation * i + offset, b'\x01\x00\x00\x00')
                if (OFFSETS_TextureAnimation_Scale.index(offset) + 1) % 2 == 0:
                    last_offset = Binary.write_offset(model)
                    seq_offsets_TextureAnimation_Scale.append(last_offset[0])
                    Binary.write_bytes(model, new_ofsTextureAnimation + M2Lengths.textureAnimation * i + offset, last_offset[1])

        if dpg.get_value("chk_TextureAnimation_Translation"):
            for seq_offset in seq_offsets_TextureAnimation_Translation:
                if (seq_offsets_TextureAnimation_Translation.index(seq_offset) + 1) % 2 == 1:
                    last_offset = Binary.write_seq_offset(model, add_n_keyframe)
                else:
                    last_offset = Binary.write_seq_offset(model, add_n_keyframe, value_bytes=b'\x00\x00\x00\x00' * 3)

                Binary.write_bytes(model, seq_offset, add_n_keyframe_bytes)
                Binary.write_bytes(model, seq_offset + 4, last_offset)

        if dpg.get_value("chk_TextureAnimation_Rotation"):
            for seq_offset in seq_offsets_TextureAnimation_Rotation:
                if (seq_offsets_TextureAnimation_Rotation.index(seq_offset) + 1) % 2 == 1:
                    last_offset = Binary.write_seq_offset(model, add_n_keyframe)
                else:
                    last_offset = Binary.write_seq_offset(model, add_n_keyframe, value_bytes=b'\xFF\x7F' * 4)

                Binary.write_bytes(model, seq_offset, add_n_keyframe_bytes)
                Binary.write_bytes(model, seq_offset + 4, last_offset)

        if dpg.get_value("chk_TextureAnimation_Scale"):
            for seq_offset in seq_offsets_TextureAnimation_Scale:
                if (seq_offsets_TextureAnimation_Scale.index(seq_offset) + 1) % 2 == 1:
                    last_offset = Binary.write_seq_offset(model, add_n_keyframe)
                else:
                    last_offset = Binary.write_seq_offset(model, add_n_keyframe, value_bytes=b'\x00\x00\x80\x3F' * 3)

                Binary.write_bytes(model, seq_offset, add_n_keyframe_bytes)
                Binary.write_bytes(model, seq_offset + 4, last_offset)

        # Даже если чекбокса нет все равно создаем 1 Timestamp и 1 Values
        else:
            for seq_offset in seq_offsets_TextureAnimation_Scale:
                if (seq_offsets_TextureAnimation_Scale.index(seq_offset) + 1) % 2 == 1:
                    last_offset = Binary.write_seq_offset(model, 1)
                else:
                    last_offset = Binary.write_seq_offset(model, 1, value_bytes=b'\x00\x00\x80\x3F' * 3)

                Binary.write_bytes(model, seq_offset, b'\x01\x00\x00\x00')
                Binary.write_bytes(model, seq_offset + 4, last_offset)

    # Добавляем пункты в TexAnimLookup
    update_nTexAnimLookup(model_path, add_n_texture_animation)

    StatusBar.success_info(f"{add_n_texture_animation} TextureAnimation created. "
                           f"Total {nTextureAnimation + add_n_texture_animation} TextureAnimation in model.")


def update_nBoneLookupTable(model_path: str, add_n_bones: int):
    with open(model_path, 'rb+') as model:
        nBoneLookup = Binary.get_int_from_bytes(model, M2Offsets.nBoneLookupTable)
        ofsBoneLookup = Binary.get_int_from_bytes(model, M2Offsets.ofsBoneLookupTable)

        if nBoneLookup > 0:
            existingBoneLookup = Binary.read_bytes(model, ofsBoneLookup, length=nBoneLookup * 2)
        else:
            existingBoneLookup = b''

        Binary.write_zeros(model)

        # Вставляем имеющиеся nBoneLookupTable
        new_ofsBoneLookup = model.seek(0, 2)
        model.write(existingBoneLookup + b'\xFF\xFF' * add_n_bones)

        # Переназначаем офсет и число nBoneLookupTable
        Binary.write_bytes(model, M2Offsets.nBoneLookupTable, (nBoneLookup + add_n_bones).to_bytes(4, 'little'))
        Binary.write_bytes(model, M2Offsets.ofsBoneLookupTable, new_ofsBoneLookup.to_bytes(4, 'little'))

        Binary.write_zeros(model)


def update_nTranslookup(model_path: str, add_n_transparency: int):
    with open(model_path, 'rb+') as model:
        nTranslookup = Binary.get_int_from_bytes(model, M2Offsets.nTransLookup)
        ofsTranslookup = Binary.get_int_from_bytes(model, M2Offsets.ofsTransLookup)

        if nTranslookup > 0:
            existingTranslookup = Binary.read_bytes(model, ofsTranslookup, length=nTranslookup * 2)
        else:
            existingTranslookup = b''

        Binary.write_zeros(model)

        # Вставляем имеющиеся Translookup
        new_ofsTranslookup = model.seek(0, 2)
        model.write(existingTranslookup + b'\x00\x00' * add_n_transparency)

        # Переназначаем офсет и число nTranslookup
        Binary.write_bytes(model, M2Offsets.nTransLookup, (nTranslookup + add_n_transparency).to_bytes(4, 'little'))
        Binary.write_bytes(model, M2Offsets.ofsTransLookup, new_ofsTranslookup.to_bytes(4, 'little'))

        Binary.write_zeros(model)


def update_nTexLookup(model_path: str, add_n_textures: int):
    with open(model_path, 'rb+') as model:
        nTextLookup = Binary.get_int_from_bytes(model, M2Offsets.nTexLookup)
        ofsTexLookup = Binary.get_int_from_bytes(model, M2Offsets.ofsTexLookup)

        if nTextLookup > 0:
            existingTextLookup = Binary.read_bytes(model, ofsTexLookup, length=nTextLookup * 2)
        else:
            existingTextLookup = b''

        Binary.write_zeros(model)

        # Вставляем имеющиеся TexLookup
        new_ofsTextLookup = model.seek(0, 2)
        model.write(existingTextLookup + b'\x00\x00' * add_n_textures * 2)

        # Переназначаем офсет и число TexLookup
        Binary.write_bytes(model, M2Offsets.nTexLookup, (nTextLookup + add_n_textures * 2).to_bytes(4, 'little'))
        Binary.write_bytes(model, M2Offsets.ofsTexLookup, new_ofsTextLookup.to_bytes(4, 'little'))

        Binary.write_zeros(model)


def update_nTexAnimLookup(model_path: str, add_n_texture_animation: int):
    with open(model_path, 'rb+') as model:
        nTexAnimLookup = Binary.get_int_from_bytes(model, M2Offsets.nTexAnimLookup)
        ofsTexAnimLookup = Binary.get_int_from_bytes(model, M2Offsets.ofsTexAnimLookup)

        if nTexAnimLookup > 0:
            existingTexAnimLookup = Binary.read_bytes(model, ofsTexAnimLookup, length=nTexAnimLookup * 2)
        else:
            existingTexAnimLookup = b''

        Binary.write_zeros(model)

        # Вставляем имеющиеся TextLookup
        new_ofsTexAnimLookup = model.seek(0, 2)
        model.write(existingTexAnimLookup + b'\xFF\xFF' * add_n_texture_animation * 2)

        # Переназначаем офсет и число TextLookup
        Binary.write_bytes(model, M2Offsets.nTexAnimLookup, (nTexAnimLookup + add_n_texture_animation * 2).to_bytes(4, 'little'))
        Binary.write_bytes(model, M2Offsets.ofsTexAnimLookup, new_ofsTexAnimLookup.to_bytes(4, 'little'))

        Binary.write_zeros(model)
