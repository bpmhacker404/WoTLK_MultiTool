import dearpygui.dearpygui as dpg
import os
import struct

from utils.binary import Binary
from utils.miscellaneous import check_model_path
from utils.offsets import M2Offsets, M2Lengths
from utils.statusbar import StatusBar


def auto_fix_helm_offset(model_path: str):
    race_id = os.path.basename(model_path)[-6:-3]
    match race_id:
        case "bef":
            x_pos = 0
            y_pos = 0
            z_pos = -0.205
        case "bem":
            x_pos = -0.08
            y_pos = 0
            z_pos = -0.17
        case "drf":
            x_pos = -0.07
            y_pos = 0
            z_pos = -0.2
        case "drm":
            x_pos = -0.075
            y_pos = 0
            z_pos = -0.255
        case "dwf":
            x_pos = 0
            y_pos = 0
            z_pos = -0.215
        case "dwm":
            x_pos = 0
            y_pos = 0
            z_pos = -0.218
        case "gnf":
            x_pos = -0.03
            y_pos = 0
            z_pos = -0.28
        case "gnm":
            x_pos = -0.025
            y_pos = 0
            z_pos = -0.26
        case "huf":
            x_pos = -0.08
            y_pos = 0
            z_pos = -0.19
        case "hum":
            x_pos = -0.07
            y_pos = 0
            z_pos = -0.215
        case "nif":
            x_pos = -0.06
            y_pos = 0
            z_pos = -0.21
        case "nim":
            x_pos = -0.095
            y_pos = 0
            z_pos = -0.18
        case "orf":
            x_pos = -0.07
            y_pos = 0
            z_pos = -0.17
        case "orm":
            x_pos = -0.15
            y_pos = 0
            z_pos = -0.18
        case "scf":
            x_pos = -0.01
            y_pos = 0
            z_pos = -0.16
        case "scm":
            x_pos = -0.125
            y_pos = 0
            z_pos = -0.135
        case "taf":
            x_pos = -0.2
            y_pos = 0
            z_pos = -0.1
        case "tam":
            x_pos = -0.225
            y_pos = 0
            z_pos = -0.1
        case "trf":
            x_pos = -0.09
            y_pos = 0
            z_pos = -0.085
        case "trm":
            x_pos = -0.12
            y_pos = 0
            z_pos = -0.165

    control_bone_id, nBones, ofsBones = get_control_bone_id(model_path)
    if control_bone_id is None:
        control_bone_id = search_valid_bone_id(model_path, nBones, ofsBones)

        if control_bone_id is None:
            control_bone_id, nBones, ofsBones = create_Control_Bone(model_path, nBones, ofsBones)

    with open(model_path, "rb+") as m2_file:
        ofsToKeyframe = Binary.get_int_from_bytes(m2_file, ofsBones + control_bone_id * M2Lengths.bone + 32)
        ofsValue = Binary.get_int_from_bytes(m2_file, ofsToKeyframe + 4)
        x = float_from_bytes(Binary.read_bytes(m2_file, ofsValue))
        x += x_pos
        y = float_from_bytes(Binary.read_bytes(m2_file, ofsValue + 4))
        y += y_pos
        z = float_from_bytes(Binary.read_bytes(m2_file, ofsValue + 8))
        z += z_pos
        pos_xyz = (x, y, z)
        Binary.write_bytes(m2_file, ofsValue, struct.pack("fff", *pos_xyz))


def create_Control_Bone(model_path: str, nBones: int, ofsBones: int) -> tuple:
    add_n_keyframe_bytes = b'\x01\x00\x00\x00'
    OFFSETS_Translation = (20, 24, 28, 32)
    OFFSETS_Rotation = (40, 44, 48, 52)
    OFFSETS_Scale = (60, 64, 68, 72)
    seq_offsets_Translation = []
    seq_offsets_Rotation = []
    seq_offsets_Scale = []

    with open(model_path, 'rb+') as model:
        md_structure = model.read(4)
        if md_structure != b'\x4D\x44\x32\x30':
            StatusBar.error_info("ERROR: Сonvert the model before editing")
            return

        # Если Bones есть копируем имеющиеся в переменную
        if nBones > 0:
            existingBones = Binary.read_bytes(model, ofsBones, length=nBones * M2Lengths.bone)
        else:
            existingBones = b''

        # Дописываем строку нулей в конце файла
        Binary.write_zeros(model)

        # Вставляем имеющиеся Bones
        new_ofsBones = model.seek(0, 2)
        model.write(existingBones + b'\xFF\xFF\xFF\xFF\x00\x02\x00\x00\xFF\xFF\x00\x00\xB1\x68\xDE\x3A'
                                    b'\x01\x00\xFF\xFF\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                                    b'\x00\x00\x00\x00\x01\x00\xFF\xFF\x00\x00\x00\x00\x00\x00\x00\x00'
                                    b'\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\xFF\xFF\x00\x00\x00\x00'
                                    b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80'
                                    b'\x00\x00\x00\x00\x00\x00\x00\x00')

        # Переназначаем офсет и число Bones
        Binary.write_bytes(model, M2Offsets.nBones, (nBones + 1).to_bytes(4, 'little'))
        Binary.write_bytes(model, M2Offsets.ofsBones, new_ofsBones.to_bytes(4, 'little'))

        # Прописываем в parent_bone id управляющей кости во все имеющиеся кости с id -1
        for i in range(nBones):
            parent_bone = Binary.read_bytes(model, new_ofsBones + M2Lengths.bone * i + 8, length=2)
            if parent_bone == b'\xFF\xFF':
                Binary.write_bytes(model, new_ofsBones + M2Lengths.bone * i + 8, nBones.to_bytes(2, 'little'))

        # Прописываем keyframes для Timestamps и Values
        for i in range(nBones, nBones + 1):
            # Timestamp
            for offset in OFFSETS_Translation:
                if (OFFSETS_Translation.index(offset) + 1) % 2 == 1:
                    Binary.write_bytes(model, new_ofsBones + M2Lengths.bone * i + offset, b'\x01\x00\x00\x00')
                if (OFFSETS_Translation.index(offset) + 1) % 2 == 0:
                    last_offset = Binary.write_offset(model)
                    seq_offsets_Translation.append(last_offset[0])
                    Binary.write_bytes(model, new_ofsBones + M2Lengths.bone * i + offset, last_offset[1])

            for offset in OFFSETS_Rotation:
                if (OFFSETS_Rotation.index(offset) + 1) % 2 == 1:
                    Binary.write_bytes(model, new_ofsBones + M2Lengths.bone * i + offset, b'\x01\x00\x00\x00')
                if (OFFSETS_Rotation.index(offset) + 1) % 2 == 0:
                    last_offset = Binary.write_offset(model)
                    seq_offsets_Rotation.append(last_offset[0])
                    Binary.write_bytes(model, new_ofsBones + M2Lengths.bone * i + offset, last_offset[1])

            for offset in OFFSETS_Scale:
                if (OFFSETS_Scale.index(offset) + 1) % 2 == 1:
                    Binary.write_bytes(model, new_ofsBones + M2Lengths.bone * i + offset, b'\x01\x00\x00\x00')
                if (OFFSETS_Scale.index(offset) + 1) % 2 == 0:
                    last_offset = Binary.write_offset(model)
                    seq_offsets_Scale.append(last_offset[0])
                    Binary.write_bytes(model, new_ofsBones + M2Lengths.bone * i + offset, last_offset[1])

            # Values
            for seq_offset in seq_offsets_Translation:
                if (seq_offsets_Translation.index(seq_offset) + 1) % 2 == 1:
                    last_offset = Binary.write_seq_offset(model, 1)
                else:
                    last_offset = Binary.write_seq_offset(model, 1, value_bytes=b'\x00\x00\x00\x00' * 3)

                Binary.write_bytes(model, seq_offset, add_n_keyframe_bytes)
                Binary.write_bytes(model, seq_offset + 4, last_offset)

            for seq_offset in seq_offsets_Rotation:
                if (seq_offsets_Rotation.index(seq_offset) + 1) % 2 == 1:
                    last_offset = Binary.write_seq_offset(model, 1)
                else:
                    last_offset = Binary.write_seq_offset(model, 1, value_bytes=b'\xFF\x7F' * 4)

                Binary.write_bytes(model, seq_offset, add_n_keyframe_bytes)
                Binary.write_bytes(model, seq_offset + 4, last_offset)

            for seq_offset in seq_offsets_Scale:
                if (seq_offsets_Scale.index(seq_offset) + 1) % 2 == 1:
                    last_offset = Binary.write_seq_offset(model, 1)
                else:
                    last_offset = Binary.write_seq_offset(model, 1, value_bytes=b'\x00\x00\x80\x3F' * 3)

                Binary.write_bytes(model, seq_offset, add_n_keyframe_bytes)
                Binary.write_bytes(model, seq_offset + 4, last_offset)

        Binary.write_zeros(model)

    return nBones, nBones + 1, new_ofsBones


def float_from_bytes(bytes_array: bytes) -> float:
    return struct.unpack('f', bytes_array)[0]


def get_control_bone_id(model_path: str) -> tuple:
    control_bone_id = None

    with open(model_path, "rb+") as m2_file:
        nBones = Binary.get_int_from_bytes(m2_file, M2Offsets.nBones)
        ofsBones = Binary.get_int_from_bytes(m2_file, M2Offsets.ofsBones)
        for i in range(nBones):
            m2_file.seek(ofsBones + i * M2Lengths.bone + 12)
            boneCRC = int.from_bytes(m2_file.read(4), "little")
            if boneCRC == 987654321:
                control_bone_id = i
                break

    return control_bone_id, nBones, ofsBones


def model_moving_pre():
    StatusBar.clear_info()

    model_path = check_model_path()
    if model_path is None:
        return

    x_pos = round(dpg.get_value("inp_x_position"), 3)
    y_pos = round(dpg.get_value("inp_y_position"), 3)
    z_pos = round(dpg.get_value("inp_z_position"), 3)

    model_moving(model_path, x_pos, y_pos, z_pos)


def model_moving(model_path: str, x_pos: float, y_pos: float, z_pos: float):
    control_bone_id, nBones, ofsBones = get_control_bone_id(model_path)
    if control_bone_id is None:
        control_bone_id = search_valid_bone_id(model_path, nBones, ofsBones)

        if control_bone_id is None:
            control_bone_id, nBones, ofsBones = create_Control_Bone(model_path, nBones, ofsBones)

    with open(model_path, "rb+") as m2_file:
        ofsToKeyframe = Binary.get_int_from_bytes(m2_file, ofsBones + control_bone_id * M2Lengths.bone + 32)
        ofsValue = Binary.get_int_from_bytes(m2_file, ofsToKeyframe + 4)
        x = float_from_bytes(Binary.read_bytes(m2_file, ofsValue))
        x += x_pos
        y = float_from_bytes(Binary.read_bytes(m2_file, ofsValue + 4))
        y += y_pos
        z = float_from_bytes(Binary.read_bytes(m2_file, ofsValue + 8))
        z += z_pos
        pos_xyz = (x, y, z)
        Binary.write_bytes(m2_file, ofsValue, struct.pack("fff", *pos_xyz))

    StatusBar.success_info("Model moved.")

    dpg.set_value("inp_x_position", 0)
    dpg.set_value("inp_y_position", 0)
    dpg.set_value("inp_z_position", 0)


def model_resize_pre():
    StatusBar.clear_info()

    model_path = check_model_path()
    if model_path is None:
        return

    percent = dpg.get_value("inp_scale_modifier")
    scaleModifier = round(1 + percent / 100, 2)
    if percent > 0:
        action = "upscaled"
    else:
        action = "downscaled"

    model_resize(model_path, scaleModifier, action)


def model_resize(model_path: str, scaleModifier: float, action: str):
    control_bone_id, nBones, ofsBones = get_control_bone_id(model_path)
    if control_bone_id is None:
        control_bone_id = search_valid_bone_id(model_path, nBones, ofsBones)

        if control_bone_id is None:
            control_bone_id, nBones, ofsBones = create_Control_Bone(model_path, nBones, ofsBones)

    with open(model_path, "rb+") as m2_file:
        ofsToKeyframe = Binary.get_int_from_bytes(m2_file, ofsBones + control_bone_id * M2Lengths.bone + 72)
        ofsValue = Binary.get_int_from_bytes(m2_file, ofsToKeyframe + 4)
        x = float_from_bytes(Binary.read_bytes(m2_file, ofsValue))
        x *= scaleModifier
        y = float_from_bytes(Binary.read_bytes(m2_file, ofsValue + 4))
        y *= scaleModifier
        z = float_from_bytes(Binary.read_bytes(m2_file, ofsValue + 8))
        z *= scaleModifier
        size_xyz = (x, y, z)
        Binary.write_bytes(m2_file, ofsValue, struct.pack("fff", *size_xyz))

    if action == "upscaled":
        coef = (scaleModifier - 1) * 100
    else:
        coef = (1 - scaleModifier) * 100

    StatusBar.success_info(f"Model {action} by {round(coef)} %")


def search_valid_bone_id(model_path: str, nBones: int, ofsBones: int) -> int:
    control_bone_id = None

    # Ищем подходящую кость с pivot point 0 0 0
    with open(model_path, "rb+") as model:
        for i in range(nBones):
            parent_bone = Binary.read_bytes(model, ofsBones + i * M2Lengths.bone + 8, length=2)
            boneCRC = Binary.read_bytes(model, ofsBones + i * M2Lengths.bone + 12)
            Translation_nKeyFrame = Binary.read_bytes(model, ofsBones + i * M2Lengths.bone + 28)
            Rotation_nKeyFrame = Binary.read_bytes(model, ofsBones + i * M2Lengths.bone + 48)
            Scale_nKeyFrame = Binary.read_bytes(model, ofsBones + i * M2Lengths.bone + 68)
            PivotPoint = Binary.read_bytes(model, ofsBones + i * M2Lengths.bone + 76, length=12)

            if (parent_bone == b'\xFF\xFF' and Translation_nKeyFrame == b'\x00\x00\x00\x00' and Rotation_nKeyFrame == b'\x00\x00\x00\x00'
                    and Scale_nKeyFrame == b'\x00\x00\x00\x00' and PivotPoint == b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                    and boneCRC != b'\xC7\x6B\x9F\x06'):
                control_bone_id = i
                break

        # Если не нашлась, ищем подходящую кость с любым pivot point
        if control_bone_id is None:
            for i in range(nBones):
                parent_bone = Binary.read_bytes(model, ofsBones + i * M2Lengths.bone + 8, length=2)
                boneCRC = Binary.read_bytes(model, ofsBones + i * M2Lengths.bone + 12)
                Translation_nKeyFrame = Binary.read_bytes(model, ofsBones + i * M2Lengths.bone + 28)
                Rotation_nKeyFrame = Binary.read_bytes(model, ofsBones + i * M2Lengths.bone + 48)
                Scale_nKeyFrame = Binary.read_bytes(model, ofsBones + i * M2Lengths.bone + 68)

                if (parent_bone == b'\xFF\xFF' and Translation_nKeyFrame == b'\x00\x00\x00\x00'
                        and Rotation_nKeyFrame == b'\x00\x00\x00\x00' and Scale_nKeyFrame == b'\x00\x00\x00\x00'
                        and boneCRC != b'\xC7\x6B\x9F\x06'):
                    control_bone_id = i
                    break

        if not control_bone_id is None:
            # Ставим флаг Transformed
            Binary.write_bytes(model, ofsBones + control_bone_id * M2Lengths.bone + 4, b'\x00\x02\x00\x00')
            # Прописываем CRC 987654321
            Binary.write_bytes(model, ofsBones + control_bone_id * M2Lengths.bone + 12, b'\xB1\x68\xDE\x3A')

            Binary.write_zeros(model)

            # Прописываем control_bone_id во все имеющиеся кости с id -1
            for i in range(nBones):
                parent_bone = Binary.read_bytes(model, ofsBones + i * M2Lengths.bone + 8, length=2)
                if parent_bone == b'\xFF\xFF' and i != control_bone_id:
                    Binary.write_bytes(model, ofsBones + M2Lengths.bone * i + 8, control_bone_id.to_bytes(2, 'little'))

            # Прописываем keyframes для Timestamps и Values
            # Timestamp
            add_n_keyframe_bytes = b'\x01\x00\x00\x00'
            OFFSETS_Translation = (20, 24, 28, 32)
            OFFSETS_Rotation = (40, 44, 48, 52)
            OFFSETS_Scale = (60, 64, 68, 72)
            seq_offsets_Translation = []
            seq_offsets_Rotation = []
            seq_offsets_Scale = []

            for offset in OFFSETS_Translation:
                if (OFFSETS_Translation.index(offset) + 1) % 2 == 1:
                    Binary.write_bytes(model, ofsBones + M2Lengths.bone * control_bone_id + offset, b'\x01\x00\x00\x00')
                if (OFFSETS_Translation.index(offset) + 1) % 2 == 0:
                    last_offset = Binary.write_offset(model)
                    seq_offsets_Translation.append(last_offset[0])
                    Binary.write_bytes(model, ofsBones + M2Lengths.bone * control_bone_id + offset, last_offset[1])

            for offset in OFFSETS_Rotation:
                if (OFFSETS_Rotation.index(offset) + 1) % 2 == 1:
                    Binary.write_bytes(model, ofsBones + M2Lengths.bone * control_bone_id + offset, b'\x01\x00\x00\x00')
                if (OFFSETS_Rotation.index(offset) + 1) % 2 == 0:
                    last_offset = Binary.write_offset(model)
                    seq_offsets_Rotation.append(last_offset[0])
                    Binary.write_bytes(model, ofsBones + M2Lengths.bone * control_bone_id + offset, last_offset[1])

            for offset in OFFSETS_Scale:
                if (OFFSETS_Scale.index(offset) + 1) % 2 == 1:
                    Binary.write_bytes(model, ofsBones + M2Lengths.bone * control_bone_id + offset, b'\x01\x00\x00\x00')
                if (OFFSETS_Scale.index(offset) + 1) % 2 == 0:
                    last_offset = Binary.write_offset(model)
                    seq_offsets_Scale.append(last_offset[0])
                    Binary.write_bytes(model, ofsBones + M2Lengths.bone * control_bone_id + offset, last_offset[1])

            # Values
            for seq_offset in seq_offsets_Translation:
                if (seq_offsets_Translation.index(seq_offset) + 1) % 2 == 1:
                    last_offset = Binary.write_seq_offset(model, 1)
                else:
                    last_offset = Binary.write_seq_offset(model, 1, value_bytes=b'\x00\x00\x00\x00' * 3)

                Binary.write_bytes(model, seq_offset, add_n_keyframe_bytes)
                Binary.write_bytes(model, seq_offset + 4, last_offset)

            for seq_offset in seq_offsets_Rotation:
                if (seq_offsets_Rotation.index(seq_offset) + 1) % 2 == 1:
                    last_offset = Binary.write_seq_offset(model, 1)
                else:
                    last_offset = Binary.write_seq_offset(model, 1, value_bytes=b'\xFF\x7F' * 4)

                Binary.write_bytes(model, seq_offset, add_n_keyframe_bytes)
                Binary.write_bytes(model, seq_offset + 4, last_offset)

            for seq_offset in seq_offsets_Scale:
                if (seq_offsets_Scale.index(seq_offset) + 1) % 2 == 1:
                    last_offset = Binary.write_seq_offset(model, 1)
                else:
                    last_offset = Binary.write_seq_offset(model, 1, value_bytes=b'\x00\x00\x80\x3F' * 3)

                Binary.write_bytes(model, seq_offset, add_n_keyframe_bytes)
                Binary.write_bytes(model, seq_offset + 4, last_offset)

            Binary.write_zeros(model)

    return control_bone_id
