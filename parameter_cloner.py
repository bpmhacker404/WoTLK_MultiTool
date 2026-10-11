from typing import BinaryIO

import dearpygui.dearpygui as dpg
import os

from utils.binary import Binary
from utils.offsets import M2Offset, M2Length
from utils.statusbar import StatusBar


class ParameterCloner:
    def __init__(self):
        self.m2From = None
        self.m2To = None
        self.isSameModel = False

    def _get_models_path(self) -> bool | None:
        m2from_path = dpg.get_value("inp_cloner_m2from")
        m2to_path = dpg.get_value("inp_cloner_m2to")

        if not m2from_path:
            StatusBar.error_info("ERROR: Select the source model.")
            return False
        if not os.path.exists(m2from_path):
            StatusBar.error_info(f"{os.path.basename(m2from_path)} not found.")
            return False
        if not m2to_path:
            StatusBar.error_info("ERROR: Select the target model.")
            return False
        if not os.path.exists(m2to_path):
            StatusBar.error_info(f"{os.path.basename(m2to_path)} not found.")
            return False

        self.m2From = m2from_path
        self.m2To = m2to_path
        self.isSameModel = m2from_path == m2to_path
        return True

    def _check_id_match_error(self, name: str, _id_from: int, _id_to: int) -> bool:
        if self.isSameModel and _id_from == _id_to:
            StatusBar.error_info(f"ERROR: the {name} IDs cannot match.")
            return True


class BoneCloner(ParameterCloner):
    def __init__(self):
        super().__init__()
        self.boneIdFrom = None
        self.boneIdTo = None
        self.m2FromNBones = 0
        self.m2ToNBones = 0
        self.m2FromOfsBones = 0
        self.m2ToOfsBones = 0

        self.transl_interp_global_seq_id_bytes = None
        self.transl_ts_n_val = []
        self.transl_ts_ofs_val = []
        self.transl_ts_seq_bytes = []
        self.transl_val_n_val = []
        self.transl_val_ofs_val = []
        self.transl_val_seq_bytes = []

        self.rot_interp_global_seq_id_bytes = None
        self.rot_ts_n_val = []
        self.rot_ts_ofs_val = []
        self.rot_ts_seq_bytes = []
        self.rot_val_n_val = []
        self.rot_val_ofs_val = []
        self.rot_val_seq_bytes = []

        self.scal_interp_global_seq_id_bytes = None
        self.scal_ts_n_val = []
        self.scal_ts_ofs_val = []
        self.scal_ts_seq_bytes = []
        self.scal_val_n_val = []
        self.scal_val_ofs_val = []
        self.scal_val_seq_bytes = []

        self.pivot_pnt_bytes = None

    def bone_copy_pre(self):
        if not self._get_models_path():
            return

        try:
            bone_id_from = int(dpg.get_value("inp_bone_from"))
            bone_id_to = int(dpg.get_value("inp_bone_to"))
        except ValueError:
            StatusBar.error_info("ERROR: Bone ID must be integer.")
            return

        if self._check_id_match_error(name="bone", _id_from=bone_id_from, _id_to=bone_id_to):
            return

        self.boneIdFrom = bone_id_from
        self.boneIdTo = bone_id_to

        self._bone_copy()

    def _bone_copy(self):
        if not self.isSameModel:
            with open(self.m2To, "rb+") as model_m2to:
                m2to_n_bones = Binary.get_int_from_bytes(model_m2to, M2Offset.nBones)
                if not m2to_n_bones > 0:
                    StatusBar.error_info(f"ERROR: There are no bones in target model.")
                    return

                self.m2ToNBones = m2to_n_bones - 1
                self.m2ToOfsBones = Binary.get_int_from_bytes(model_m2to, M2Offset.ofsBones)

        with open(self.m2From, "rb+") as model_m2from:
            m2from_n_bones = Binary.get_int_from_bytes(model_m2from, M2Offset.nBones)
            if not m2from_n_bones > 0:
                StatusBar.error_info(f"ERROR: There are no bones in model.")
                return

            self.m2FromNBones = m2from_n_bones - 1

            if self.isSameModel:
                self.m2ToNBones = self.m2FromNBones
                if self.boneIdFrom > self.m2FromNBones or self.boneIdTo > self.m2FromNBones:
                    StatusBar.error_info(f"ERROR: There is no such bone ID in the model.")
                    return

            if not self.isSameModel:
                if self.boneIdFrom > self.m2FromNBones or self.boneIdTo > self.m2ToNBones:
                    StatusBar.error_info(f"ERROR: There is no such bone ID in the model.")
                    return

            self.m2FromOfsBones = Binary.get_int_from_bytes(model_m2from, M2Offset.ofsBones)

            transl_n_ts_pairs = Binary.get_int_from_bytes(model_m2from, self.m2FromOfsBones + M2Length.bone * self.boneIdFrom + 20)
            transl_n_kf_pairs = Binary.get_int_from_bytes(model_m2from, self.m2FromOfsBones + M2Length.bone * self.boneIdFrom + 28)
            rotation_n_ts_pairs = Binary.get_int_from_bytes(model_m2from, self.m2FromOfsBones + M2Length.bone * self.boneIdFrom + 40)
            rotation_n_kf_pairs = Binary.get_int_from_bytes(model_m2from, self.m2FromOfsBones + M2Length.bone * self.boneIdFrom + 48)
            scaling_n_ts_pairs = Binary.get_int_from_bytes(model_m2from, self.m2FromOfsBones + M2Length.bone * self.boneIdFrom + 60)
            scaling_n_kf_pairs = Binary.get_int_from_bytes(model_m2from, self.m2FromOfsBones + M2Length.bone * self.boneIdFrom + 68)

            if (transl_n_ts_pairs < 1 and transl_n_kf_pairs < 1 and rotation_n_ts_pairs < 1 and
                    rotation_n_kf_pairs < 1 and scaling_n_ts_pairs < 1 and scaling_n_kf_pairs < 1):
                StatusBar.error_info(f"ERROR: Nothing to copy. Bone {self.boneIdFrom} is empty.")
                return

            # ? В зависимости от чекбоксов и наличия keyframes копируем и вставляем значения ----------------------------------------------
            if dpg.get_value("chk_bone_cloner_Translation") and transl_n_ts_pairs > 0 and transl_n_kf_pairs > 0:
                self._bone_copy_translation(model_m2from, transl_n_ts_pairs, transl_n_kf_pairs)
                if self.isSameModel:
                    self._bone_paste_translation(model_m2from, self.m2FromOfsBones, transl_n_ts_pairs, transl_n_kf_pairs)

            if dpg.get_value("chk_bone_cloner_Rotation") and rotation_n_ts_pairs > 0 and rotation_n_kf_pairs > 0:
                self._bone_copy_rotation(model_m2from, rotation_n_ts_pairs, rotation_n_kf_pairs)
                if self.isSameModel:
                    self._bone_paste_rotation(model_m2from, self.m2FromOfsBones, rotation_n_ts_pairs, rotation_n_kf_pairs)

            if dpg.get_value("chk_bone_cloner_Scale") and scaling_n_ts_pairs > 0 and scaling_n_kf_pairs > 0:
                self._bone_copy_scaling(model_m2from, scaling_n_ts_pairs, scaling_n_kf_pairs)
                if self.isSameModel:
                    self._bone_paste_scaling(model_m2from, self.m2FromOfsBones, scaling_n_ts_pairs, scaling_n_kf_pairs)

            if dpg.get_value("chk_bone_cloner_PivotPoint"):
                self.pivot_pnt_bytes = Binary.read_bytes(model_m2from, self.m2FromOfsBones + M2Length.bone * self.boneIdFrom + 76,
                                                         length=12)
                if self.isSameModel:
                    Binary.write_bytes(model_m2from, self.m2FromOfsBones + M2Length.bone * self.boneIdTo + 76, self.pivot_pnt_bytes)

        # ? Если модели разные вставляем уже в другую модель ------------------------------------------------------------------------------
        if not self.isSameModel:
            with open(self.m2To, "rb+") as model_m2to:
                if dpg.get_value("chk_bone_cloner_Translation") and transl_n_ts_pairs > 0 and transl_n_kf_pairs > 0:
                    self._bone_paste_translation(model_m2to, self.m2ToOfsBones, transl_n_ts_pairs, transl_n_kf_pairs)

                if dpg.get_value("chk_bone_cloner_Rotation") and rotation_n_ts_pairs > 0 and rotation_n_kf_pairs > 0:
                    self._bone_paste_rotation(model_m2to, self.m2ToOfsBones, rotation_n_ts_pairs, rotation_n_kf_pairs)

                if dpg.get_value("chk_bone_cloner_Scale") and scaling_n_ts_pairs > 0 and scaling_n_kf_pairs > 0:
                    self._bone_paste_scaling(model_m2to, self.m2ToOfsBones, scaling_n_ts_pairs, scaling_n_kf_pairs)

                if dpg.get_value("chk_bone_cloner_PivotPoint"):
                    Binary.write_bytes(model_m2to, self.m2ToOfsBones + M2Length.bone * self.boneIdTo + 76, self.pivot_pnt_bytes)

        StatusBar.success_info(f"Bone {self.boneIdFrom} -> {self.boneIdTo} copied successfully.")

    def _bone_copy_translation(self, model_: BinaryIO, number_of_timestamp_pairs_: int, number_of_keyframe_pairs_: int):
        self.transl_interp_global_seq_id_bytes = Binary.read_bytes(model_, self.m2FromOfsBones + M2Length.bone * self.boneIdFrom + 16)

        number_of_ts_pairs_ofs = Binary.get_int_from_bytes(model_, self.m2FromOfsBones + M2Length.bone * self.boneIdFrom + 24)
        number_of_kf_pairs_ofs = Binary.get_int_from_bytes(model_, self.m2FromOfsBones + M2Length.bone * self.boneIdFrom + 32)

        for i in range(number_of_timestamp_pairs_):
            self.transl_ts_n_val.append(Binary.get_int_from_bytes(model_, number_of_ts_pairs_ofs + i * 8))
            self.transl_ts_ofs_val.append(Binary.get_int_from_bytes(model_, number_of_ts_pairs_ofs + i * 8 + 4))

        for i_ in range(number_of_keyframe_pairs_):
            self.transl_val_n_val.append(Binary.get_int_from_bytes(model_, number_of_kf_pairs_ofs + i_ * 8))
            self.transl_val_ofs_val.append(Binary.get_int_from_bytes(model_, number_of_kf_pairs_ofs + i_ * 8 + 4))

        for i2 in range(len(self.transl_ts_n_val)):
            self.transl_ts_seq_bytes.append(
                Binary.read_bytes(model_, self.transl_ts_ofs_val[i2], self.transl_ts_n_val[i2] * 4))

        for i2_ in range(len(self.transl_ts_n_val)):
            self.transl_val_seq_bytes.append(
                Binary.read_bytes(model_, self.transl_val_ofs_val[i2_], self.transl_val_n_val[i2_] * 12))

    def _bone_paste_translation(self, model_: BinaryIO, OfsBones_: int, number_of_ts_pairs_: int, number_of_kf_pairs_: int):
        Binary.write_bytes(model_, OfsBones_ + M2Length.bone * self.boneIdTo + 16, self.transl_interp_global_seq_id_bytes)

        # numberOfTimestampPairs
        Binary.write_bytes(model_, OfsBones_ + M2Length.bone * self.boneIdTo + 20, number_of_ts_pairs_.to_bytes(4, byteorder='little'))

        Binary.write_zeros(model_)

        last_offset1 = model_.seek(0, 2)
        Binary.write_bytes(model_, last_offset1, b'\x00\x00\x00\x00\x00\x00\x00\x00' * number_of_ts_pairs_)
        Binary.write_bytes(model_, OfsBones_ + M2Length.bone * self.boneIdTo + 24, last_offset1.to_bytes(4, byteorder='little'))

        Binary.write_zeros(model_)

        # numberOfKeyFramePairs
        Binary.write_bytes(model_, OfsBones_ + M2Length.bone * self.boneIdTo + 28, number_of_kf_pairs_.to_bytes(4, byteorder='little'))
        last_offset2 = model_.seek(0, 2)
        Binary.write_bytes(model_, last_offset2, b'\x00\x00\x00\x00\x00\x00\x00\x00' * number_of_kf_pairs_)
        Binary.write_bytes(model_, OfsBones_ + M2Length.bone * self.boneIdTo + 32, last_offset2.to_bytes(4, byteorder='little'))

        Binary.write_zeros(model_)

        for i3 in range(number_of_ts_pairs_):  # Timestamps
            Binary.write_bytes(model_, last_offset1 + i3 * 8, self.transl_ts_n_val[i3].to_bytes(4, byteorder='little'))
            last_offset = model_.seek(0, 2)
            Binary.write_bytes(model_, last_offset1 + i3 * 8 + 4, last_offset.to_bytes(4, byteorder='little'))
            Binary.write_bytes(model_, last_offset, self.transl_ts_seq_bytes[i3])

        for i3_ in range(number_of_ts_pairs_):  # Values
            Binary.write_bytes(model_, last_offset2 + i3_ * 8, self.transl_val_n_val[i3_].to_bytes(4, byteorder='little'))
            last_offset_ = model_.seek(0, 2)
            Binary.write_bytes(model_, last_offset2 + i3_ * 8 + 4, last_offset_.to_bytes(4, byteorder='little'))
            Binary.write_bytes(model_, last_offset_, self.transl_val_seq_bytes[i3_])

        Binary.write_zeros(model_)

    def _bone_copy_rotation(self, model_: BinaryIO, number_of_timestamp_pairs_: int, number_of_keyframe_pairs_: int):
        self.rot_interp_global_seq_id_bytes = Binary.read_bytes(model_, self.m2FromOfsBones + M2Length.bone * self.boneIdFrom + 36)

        number_of_ts_pairs_ofs = Binary.get_int_from_bytes(model_, self.m2FromOfsBones + M2Length.bone * self.boneIdFrom + 44)
        number_of_kf_pairs_ofs = Binary.get_int_from_bytes(model_, self.m2FromOfsBones + M2Length.bone * self.boneIdFrom + 52)

        for i in range(number_of_timestamp_pairs_):
            self.rot_ts_n_val.append(Binary.get_int_from_bytes(model_, number_of_ts_pairs_ofs + i * 8))
            self.rot_ts_ofs_val.append(Binary.get_int_from_bytes(model_, number_of_ts_pairs_ofs + i * 8 + 4))

        for i_ in range(number_of_keyframe_pairs_):
            self.rot_val_n_val.append(Binary.get_int_from_bytes(model_, number_of_kf_pairs_ofs + i_ * 8))
            self.rot_val_ofs_val.append(Binary.get_int_from_bytes(model_, number_of_kf_pairs_ofs + i_ * 8 + 4))

        for i2 in range(len(self.rot_ts_n_val)):
            self.rot_ts_seq_bytes.append(Binary.read_bytes(model_, self.rot_ts_ofs_val[i2], self.rot_ts_n_val[i2] * 4))

        for i2_ in range(len(self.rot_ts_n_val)):
            self.rot_val_seq_bytes.append(Binary.read_bytes(model_, self.rot_val_ofs_val[i2_], self.rot_val_n_val[i2_] * 8))

    def _bone_paste_rotation(self, model_: BinaryIO, OfsBones_: int, number_of_ts_pairs_: int, number_of_kf_pairs_: int):
        Binary.write_bytes(model_, OfsBones_ + M2Length.bone * self.boneIdTo + 36, self.rot_interp_global_seq_id_bytes)

        # numberOfTimestampPairs
        Binary.write_bytes(model_, OfsBones_ + M2Length.bone * self.boneIdTo + 40, number_of_ts_pairs_.to_bytes(4, byteorder='little'))

        Binary.write_zeros(model_)

        last_offset1 = model_.seek(0, 2)
        Binary.write_bytes(model_, last_offset1, b'\x00\x00\x00\x00\x00\x00\x00\x00' * number_of_ts_pairs_)
        Binary.write_bytes(model_, OfsBones_ + M2Length.bone * self.boneIdTo + 44, last_offset1.to_bytes(4, byteorder='little'))

        Binary.write_zeros(model_)

        # numberOfKeyFramePairs
        Binary.write_bytes(model_, OfsBones_ + M2Length.bone * self.boneIdTo + 48, number_of_kf_pairs_.to_bytes(4, byteorder='little'))
        last_offset2 = model_.seek(0, 2)
        Binary.write_bytes(model_, last_offset2, b'\x00\x00\x00\x00\x00\x00\x00\x00' * number_of_kf_pairs_)
        Binary.write_bytes(model_, OfsBones_ + M2Length.bone * self.boneIdTo + 52, last_offset2.to_bytes(4, byteorder='little'))

        Binary.write_zeros(model_)

        for i3 in range(number_of_ts_pairs_):  # Timestamps
            Binary.write_bytes(model_, last_offset1 + i3 * 8, self.rot_ts_n_val[i3].to_bytes(4, byteorder='little'))
            last_offset = model_.seek(0, 2)
            Binary.write_bytes(model_, last_offset1 + i3 * 8 + 4, last_offset.to_bytes(4, byteorder='little'))
            Binary.write_bytes(model_, last_offset, self.rot_ts_seq_bytes[i3])

        for i3_ in range(number_of_ts_pairs_):  # Values
            Binary.write_bytes(model_, last_offset2 + i3_ * 8, self.rot_val_n_val[i3_].to_bytes(4, byteorder='little'))
            last_offset_ = model_.seek(0, 2)
            Binary.write_bytes(model_, last_offset2 + i3_ * 8 + 4, last_offset_.to_bytes(4, byteorder='little'))
            Binary.write_bytes(model_, last_offset_, self.rot_val_seq_bytes[i3_])

        Binary.write_zeros(model_)

    def _bone_copy_scaling(self, model_: BinaryIO, number_of_ts_pairs_: int, number_of_kf_pairs_: int):
        self.scal_interp_global_seq_id_bytes = Binary.read_bytes(model_, self.m2FromOfsBones + M2Length.bone * self.boneIdFrom + 56)

        number_of_ts_pairs_ofs = Binary.get_int_from_bytes(model_, self.m2FromOfsBones + M2Length.bone * self.boneIdFrom + 64)
        number_of_kf_pairs_ofs = Binary.get_int_from_bytes(model_, self.m2FromOfsBones + M2Length.bone * self.boneIdFrom + 72)

        for i in range(number_of_ts_pairs_):
            self.scal_ts_n_val.append(Binary.get_int_from_bytes(model_, number_of_ts_pairs_ofs + i * 8))
            self.scal_ts_ofs_val.append(Binary.get_int_from_bytes(model_, number_of_ts_pairs_ofs + i * 8 + 4))

        for i_ in range(number_of_kf_pairs_):
            self.scal_val_n_val.append(Binary.get_int_from_bytes(model_, number_of_kf_pairs_ofs + i_ * 8))
            self.scal_val_ofs_val.append(Binary.get_int_from_bytes(model_, number_of_kf_pairs_ofs + i_ * 8 + 4))

        for i2 in range(len(self.scal_ts_n_val)):
            self.scal_ts_seq_bytes.append(Binary.read_bytes(model_, self.scal_ts_ofs_val[i2], self.scal_ts_n_val[i2] * 4))

        for i2_ in range(len(self.scal_ts_n_val)):
            self.scal_val_seq_bytes.append(Binary.read_bytes(model_, self.scal_val_ofs_val[i2_], self.scal_val_n_val[i2_] * 12))

    def _bone_paste_scaling(self, model_: BinaryIO, OfsBones_: int, number_of_ts_pairs_: int, number_of_kf_pairs_: int):
        Binary.write_bytes(model_, OfsBones_ + M2Length.bone * self.boneIdTo + 56, self.scal_interp_global_seq_id_bytes)

        # numberOfTimestampPairs
        Binary.write_bytes(model_, OfsBones_ + M2Length.bone * self.boneIdTo + 60, number_of_ts_pairs_.to_bytes(4, byteorder='little'))

        Binary.write_zeros(model_)

        last_offset1 = model_.seek(0, 2)
        Binary.write_bytes(model_, last_offset1, b'\x00\x00\x00\x00\x00\x00\x00\x00' * number_of_ts_pairs_)
        Binary.write_bytes(model_, OfsBones_ + M2Length.bone * self.boneIdTo + 64, last_offset1.to_bytes(4, byteorder='little'))

        Binary.write_zeros(model_)

        # numberOfKeyFramePairs
        Binary.write_bytes(model_, OfsBones_ + M2Length.bone * self.boneIdTo + 68, number_of_kf_pairs_.to_bytes(4, byteorder='little'))
        last_offset2 = model_.seek(0, 2)
        Binary.write_bytes(model_, last_offset2, b'\x00\x00\x00\x00\x00\x00\x00\x00' * number_of_kf_pairs_)
        Binary.write_bytes(model_, OfsBones_ + M2Length.bone * self.boneIdTo + 72, last_offset2.to_bytes(4, byteorder='little'))

        Binary.write_zeros(model_)

        for i3 in range(number_of_ts_pairs_):  # Timestamps
            Binary.write_bytes(model_, last_offset1 + i3 * 8, self.scal_ts_n_val[i3].to_bytes(4, byteorder='little'))
            last_offset = model_.seek(0, 2)
            Binary.write_bytes(model_, last_offset1 + i3 * 8 + 4, last_offset.to_bytes(4, byteorder='little'))
            Binary.write_bytes(model_, last_offset, self.scal_ts_seq_bytes[i3])

        for i3_ in range(number_of_ts_pairs_):  # Values
            Binary.write_bytes(model_, last_offset2 + i3_ * 8, self.scal_val_n_val[i3_].to_bytes(4, byteorder='little'))
            last_offset_ = model_.seek(0, 2)
            Binary.write_bytes(model_, last_offset2 + i3_ * 8 + 4, last_offset_.to_bytes(4, byteorder='little'))
            Binary.write_bytes(model_, last_offset_, self.scal_val_seq_bytes[i3_])

        Binary.write_zeros(model_)


class ColorCloner(ParameterCloner):
    def __init__(self):
        super().__init__()
        self.colorIdFrom = None
        self.colorIdTo = None
        self.m2FromNColor = 0
        self.m2ToNColor = 0
        self.m2FromOfsColor = 0
        self.m2ToOfsColor = 0

        self.color_interp_global_seq_id_bytes = None
        self.color_ts_n_val = []
        self.color_ts_ofs_val = []
        self.color_val_n_val = []
        self.color_val_ofs_val = []
        self.color_ts_seq_bytes = []
        self.color_val_seq_bytes = []

        self.alpha_interp_global_seq_id_bytes = None
        self.alpha_ts_n_val = []
        self.alpha_ts_ofs_val = []
        self.alpha_val_n_val = []
        self.alpha_val_ofs_val = []
        self.alpha_ts_seq_bytes = []
        self.alpha_val_seq_bytes = []

    def color_copy_pre(self):
        if not self._get_models_path():
            return

        try:
            color_id_from = int(dpg.get_value("inp_color_from"))
            color_id_to = int(dpg.get_value("inp_color_to"))
        except ValueError:
            StatusBar.error_info("ERROR: Color ID must be integer.")
            return

        if self._check_id_match_error(name="color", _id_from=color_id_from, _id_to=color_id_to):
            return

        self.colorIdFrom = color_id_from
        self.colorIdTo = color_id_to

        self._color_copy()

    def _color_copy(self):
        if not self.isSameModel:
            with open(self.m2To, "rb+") as model_m2to:
                m2to_n_color = Binary.get_int_from_bytes(model_m2to, M2Offset.nColors)
                if not m2to_n_color > 0:
                    StatusBar.error_info(f"ERROR: There are no colors in target model.")
                    return

                self.m2ToNColor = m2to_n_color - 1
                self.m2ToOfsColor = Binary.get_int_from_bytes(model_m2to, M2Offset.ofsColors)

        with open(self.m2From, "rb+") as model_m2from:
            m2from_n_color = Binary.get_int_from_bytes(model_m2from, M2Offset.nColors)
            if not m2from_n_color > 0:
                StatusBar.error_info(f"ERROR: There are no colors in model.")
                return

            self.m2FromNColor = m2from_n_color - 1

            if self.isSameModel:
                self.m2ToNColor = self.m2FromNColor
                if self.colorIdFrom > self.m2FromNColor or self.colorIdTo > self.m2FromNColor:
                    StatusBar.error_info(f"ERROR: There is no such color ID in the model.")
                    return

            if not self.isSameModel:
                if self.colorIdFrom > self.m2FromNColor or self.colorIdTo > self.m2ToNColor:
                    StatusBar.error_info(f"ERROR: There is no such color ID in the model.")
                    return

            self.m2FromOfsColor = Binary.get_int_from_bytes(model_m2from, M2Offset.ofsColors)

            color_n_ts_pairs = Binary.get_int_from_bytes(model_m2from, self.m2FromOfsColor + M2Length.color * self.colorIdFrom + 4)
            color_n_kf_pairs = Binary.get_int_from_bytes(model_m2from, self.m2FromOfsColor + M2Length.color * self.colorIdFrom + 12)
            alpha_n_ts_pairs = Binary.get_int_from_bytes(model_m2from, self.m2FromOfsColor + M2Length.color * self.colorIdFrom + 24)
            alpha_n_kf_pairs = Binary.get_int_from_bytes(model_m2from, self.m2FromOfsColor + M2Length.color * self.colorIdFrom + 32)

            if color_n_ts_pairs < 1 and color_n_kf_pairs < 1 and alpha_n_ts_pairs < 1 and alpha_n_kf_pairs < 1:
                StatusBar.error_info(f"ERROR: Nothing to copy. Color {self.colorIdFrom} is empty.")
                return

            # ? В зависимости от чекбоксов и наличия keyframes копируем и вставляем значения ----------------------------------------------
            if dpg.get_value("chk_color_cloner_Color") and color_n_ts_pairs > 0 and color_n_kf_pairs > 0:
                self._color_copy_color(model_m2from, color_n_ts_pairs, color_n_kf_pairs)
                if self.isSameModel:
                    self._color_paste_color(model_m2from, self.m2FromOfsColor, color_n_ts_pairs, color_n_kf_pairs)

            if dpg.get_value("chk_color_cloner_Alpha") and alpha_n_ts_pairs > 0 and alpha_n_kf_pairs > 0:
                self._color_copy_alpha(model_m2from, alpha_n_ts_pairs, alpha_n_kf_pairs)
                if self.isSameModel:
                    self._color_paste_alpha(model_m2from, self.m2FromOfsColor, alpha_n_ts_pairs, alpha_n_kf_pairs)

        if not self.isSameModel:
            with open(self.m2To, "rb+") as model_m2to:
                if dpg.get_value("chk_color_cloner_Color") and color_n_ts_pairs > 0 and color_n_kf_pairs > 0:
                    self._color_paste_color(model_m2to, self.m2ToOfsColor, color_n_ts_pairs, color_n_kf_pairs)

                if dpg.get_value("chk_color_cloner_Alpha") and alpha_n_ts_pairs > 0 and alpha_n_kf_pairs > 0:
                    self._color_paste_alpha(model_m2to, self.m2ToOfsColor, alpha_n_ts_pairs, alpha_n_kf_pairs)

        StatusBar.success_info(f"Color {self.colorIdFrom} -> {self.colorIdTo} copied successfully.")

    def _color_copy_color(self, model_: BinaryIO, number_of_timestamp_pairs_: int, number_of_keyframe_pairs_: int):
        self.color_interp_global_seq_id_bytes = Binary.read_bytes(model_, self.m2FromOfsColor + M2Length.color * self.colorIdFrom)

        number_of_ts_pairs_ofs = Binary.get_int_from_bytes(model_, self.m2FromOfsColor + M2Length.color * self.colorIdFrom + 8)
        number_of_kf_pairs_ofs = Binary.get_int_from_bytes(model_, self.m2FromOfsColor + M2Length.color * self.colorIdFrom + 16)

        for i in range(number_of_timestamp_pairs_):
            self.color_ts_n_val.append(Binary.get_int_from_bytes(model_, number_of_ts_pairs_ofs + i * 8))
            self.color_ts_ofs_val.append(Binary.get_int_from_bytes(model_, number_of_ts_pairs_ofs + i * 8 + 4))

        for i_ in range(number_of_keyframe_pairs_):
            self.color_val_n_val.append(Binary.get_int_from_bytes(model_, number_of_kf_pairs_ofs + i_ * 8))
            self.color_val_ofs_val.append(Binary.get_int_from_bytes(model_, number_of_kf_pairs_ofs + i_ * 8 + 4))

        for i2 in range(len(self.color_ts_n_val)):
            self.color_ts_seq_bytes.append(Binary.read_bytes(model_, self.color_ts_ofs_val[i2], self.color_ts_n_val[i2] * 4))

        for i2_ in range(len(self.color_ts_n_val)):
            self.color_val_seq_bytes.append(Binary.read_bytes(model_, self.color_val_ofs_val[i2_], self.color_val_n_val[i2_] * 12))

    def _color_paste_color(self, model_: BinaryIO, OfsColor_: int, number_of_ts_pairs_: int, number_of_kf_pairs_: int):
        Binary.write_bytes(model_, OfsColor_ + M2Length.color * self.colorIdTo, self.color_interp_global_seq_id_bytes)

        # numberOfTimestampPairs
        Binary.write_bytes(model_, OfsColor_ + M2Length.color * self.colorIdTo + 4, number_of_ts_pairs_.to_bytes(4, byteorder='little'))

        Binary.write_zeros(model_)

        last_offset1 = model_.seek(0, 2)
        Binary.write_bytes(model_, last_offset1, b'\x00\x00\x00\x00\x00\x00\x00\x00' * number_of_ts_pairs_)
        Binary.write_bytes(model_, OfsColor_ + M2Length.color * self.colorIdTo + 8, last_offset1.to_bytes(4, byteorder='little'))

        Binary.write_zeros(model_)

        # numberOfKeyFramePairs
        Binary.write_bytes(model_, OfsColor_ + M2Length.color * self.colorIdTo + 12, number_of_kf_pairs_.to_bytes(4, byteorder='little'))
        last_offset2 = model_.seek(0, 2)
        Binary.write_bytes(model_, last_offset2, b'\x00\x00\x00\x00\x00\x00\x00\x00' * number_of_kf_pairs_)
        Binary.write_bytes(model_, OfsColor_ + M2Length.color * self.colorIdTo + 16, last_offset2.to_bytes(4, byteorder='little'))

        Binary.write_zeros(model_)

        for i3 in range(number_of_ts_pairs_):  # Timestamps
            Binary.write_bytes(model_, last_offset1 + i3 * 8, self.color_ts_n_val[i3].to_bytes(4, byteorder='little'))
            last_offset = model_.seek(0, 2)
            Binary.write_bytes(model_, last_offset1 + i3 * 8 + 4, last_offset.to_bytes(4, byteorder='little'))
            Binary.write_bytes(model_, last_offset, self.color_ts_seq_bytes[i3])

        for i3_ in range(number_of_ts_pairs_):  # Values
            Binary.write_bytes(model_, last_offset2 + i3_ * 8, self.color_val_n_val[i3_].to_bytes(4, byteorder='little'))
            last_offset_ = model_.seek(0, 2)
            Binary.write_bytes(model_, last_offset2 + i3_ * 8 + 4, last_offset_.to_bytes(4, byteorder='little'))
            Binary.write_bytes(model_, last_offset_, self.color_val_seq_bytes[i3_])

        Binary.write_zeros(model_)

    def _color_copy_alpha(self, model_: BinaryIO, number_of_timestamp_pairs_: int, number_of_keyframe_pairs_: int):
        self.alpha_interp_global_seq_id_bytes = Binary.read_bytes(model_, self.m2FromOfsColor + M2Length.color * self.colorIdFrom + 20)

        number_of_ts_pairs_ofs = Binary.get_int_from_bytes(model_, self.m2FromOfsColor + M2Length.color * self.colorIdFrom + 28)
        number_of_kf_pairs_ofs = Binary.get_int_from_bytes(model_, self.m2FromOfsColor + M2Length.color * self.colorIdFrom + 36)

        for i in range(number_of_timestamp_pairs_):
            self.alpha_ts_n_val.append(Binary.get_int_from_bytes(model_, number_of_ts_pairs_ofs + i * 8))
            self.alpha_ts_ofs_val.append(Binary.get_int_from_bytes(model_, number_of_ts_pairs_ofs + i * 8 + 4))

        for i_ in range(number_of_keyframe_pairs_):
            self.alpha_val_n_val.append(Binary.get_int_from_bytes(model_, number_of_kf_pairs_ofs + i_ * 8))
            self.alpha_val_ofs_val.append(Binary.get_int_from_bytes(model_, number_of_kf_pairs_ofs + i_ * 8 + 4))

        for i2 in range(len(self.alpha_ts_n_val)):
            self.alpha_ts_seq_bytes.append(Binary.read_bytes(model_, self.alpha_ts_ofs_val[i2], self.alpha_ts_n_val[i2] * 4))

        for i2_ in range(len(self.alpha_ts_n_val)):
            self.alpha_val_seq_bytes.append(Binary.read_bytes(model_, self.alpha_val_ofs_val[i2_], self.alpha_val_n_val[i2_] * 2))

    def _color_paste_alpha(self, model_: BinaryIO, OfsColor_: int, number_of_ts_pairs_: int, number_of_kf_pairs_: int):
        Binary.write_bytes(model_, OfsColor_ + M2Length.color * self.colorIdTo + 20, self.alpha_interp_global_seq_id_bytes)

        # numberOfTimestampPairs
        Binary.write_bytes(model_, OfsColor_ + M2Length.color * self.colorIdTo + 24, number_of_ts_pairs_.to_bytes(4, byteorder='little'))

        Binary.write_zeros(model_)

        last_offset1 = model_.seek(0, 2)
        Binary.write_bytes(model_, last_offset1, b'\x00\x00\x00\x00\x00\x00\x00\x00' * number_of_ts_pairs_)
        Binary.write_bytes(model_, OfsColor_ + M2Length.color * self.colorIdTo + 28, last_offset1.to_bytes(4, byteorder='little'))

        Binary.write_zeros(model_)

        # numberOfKeyFramePairs
        Binary.write_bytes(model_, OfsColor_ + M2Length.color * self.colorIdTo + 32, number_of_kf_pairs_.to_bytes(4, byteorder='little'))
        last_offset2 = model_.seek(0, 2)
        Binary.write_bytes(model_, last_offset2, b'\x00\x00\x00\x00\x00\x00\x00\x00' * number_of_kf_pairs_)
        Binary.write_bytes(model_, OfsColor_ + M2Length.color * self.colorIdTo + 36, last_offset2.to_bytes(4, byteorder='little'))

        Binary.write_zeros(model_)

        for i3 in range(number_of_ts_pairs_):  # Timestamps
            Binary.write_bytes(model_, last_offset1 + i3 * 8, self.alpha_ts_n_val[i3].to_bytes(4, byteorder='little'))
            last_offset = model_.seek(0, 2)
            Binary.write_bytes(model_, last_offset1 + i3 * 8 + 4, last_offset.to_bytes(4, byteorder='little'))
            Binary.write_bytes(model_, last_offset, self.alpha_ts_seq_bytes[i3])

        for i3_ in range(number_of_ts_pairs_):  # Values
            Binary.write_bytes(model_, last_offset2 + i3_ * 8, self.alpha_val_n_val[i3_].to_bytes(4, byteorder='little'))
            last_offset_ = model_.seek(0, 2)
            Binary.write_bytes(model_, last_offset2 + i3_ * 8 + 4, last_offset_.to_bytes(4, byteorder='little'))
            Binary.write_bytes(model_, last_offset_, self.alpha_val_seq_bytes[i3_])

        Binary.write_zeros(model_)


class TransparencyCloner(ParameterCloner):
    def __init__(self):
        super().__init__()
        self.transpIdFrom = None
        self.transpIdTo = None
        self.m2FromNTransp = 0
        self.m2ToNTransp = 0
        self.m2FromOfsTransp = 0
        self.m2ToOfsTransp = 0

        self.transp_interp_global_seq_id_bytes = None
        self.transp_ts_n_val = []
        self.transp_ts_ofs_val = []
        self.transp_ts_seq_bytes = []
        self.transp_val_n_val = []
        self.transp_val_ofs_val = []
        self.transp_val_seq_bytes = []

    def transp_copy_pre(self):
        if not self._get_models_path():
            return

        try:
            transp_id_from = int(dpg.get_value("inp_transp_from"))
            transp_id_to = int(dpg.get_value("inp_transp_to"))
        except ValueError:
            StatusBar.error_info("ERROR: Transparency ID must be integer.")
            return

        if self._check_id_match_error(name="bone", _id_from=transp_id_from, _id_to=transp_id_to):
            return

        self.transpIdFrom = transp_id_from
        self.transpIdTo = transp_id_to

        self._transp_copy()

    def _transp_copy(self):
        if not self.isSameModel:
            with open(self.m2To, "rb+") as model_m2to:
                m2to_n_transp = Binary.get_int_from_bytes(model_m2to, M2Offset.nTransp)
                if not m2to_n_transp > 0:
                    StatusBar.error_info(f"ERROR: There are no bones in target model.")
                    return

                self.m2ToNTransp = m2to_n_transp - 1
                self.m2ToOfsTransp = Binary.get_int_from_bytes(model_m2to, M2Offset.ofsTransp)

        with open(self.m2From, "rb+") as model_m2from:
            m2from_n_transp = Binary.get_int_from_bytes(model_m2from, M2Offset.nTransp)
            if not m2from_n_transp > 0:
                StatusBar.error_info(f"ERROR: There are no transparency in model.")
                return

            self.m2FromNTransp = m2from_n_transp - 1

            if self.isSameModel:
                self.m2ToNTransp = self.m2FromNTransp
                if self.transpIdFrom > self.m2FromNTransp or self.transpIdTo > self.m2ToNTransp:
                    StatusBar.error_info(f"ERROR: There is no such transparency ID in the model.")
                    return

            if not self.isSameModel:
                if self.transpIdFrom > self.m2FromNTransp or self.transpIdTo > self.m2ToNTransp:
                    StatusBar.error_info(f"ERROR: There is no such transparency ID in the model.")
                    return

            self.m2FromOfsTransp = Binary.get_int_from_bytes(model_m2from, M2Offset.ofsTransp)

            transp_n_ts_pairs = Binary.get_int_from_bytes(model_m2from, self.m2FromOfsTransp + M2Length.transp * self.transpIdFrom + 4)
            transp_n_kf_pairs = Binary.get_int_from_bytes(model_m2from, self.m2FromOfsTransp + M2Length.transp * self.transpIdFrom + 12)

            if transp_n_ts_pairs < 1 and transp_n_kf_pairs < 1:
                StatusBar.error_info(f"ERROR: Nothing to copy. Transparency {self.transpIdFrom} is empty.")
                return

            self._transp_copy_transp(model_m2from, transp_n_ts_pairs, transp_n_kf_pairs)
            if self.isSameModel:
                self._transp_paste_transp(model_m2from, self.m2FromOfsTransp, transp_n_ts_pairs, transp_n_kf_pairs)

        if not self.isSameModel:
            with open(self.m2To, "rb+") as model_m2to:
                self._transp_paste_transp(model_m2to, self.m2ToOfsTransp, transp_n_ts_pairs, transp_n_kf_pairs)

        StatusBar.success_info(f"Transparency {self.transpIdFrom} -> {self.transpIdTo} copied successfully.")

    def _transp_copy_transp(self, model_: BinaryIO, number_of_timestamp_pairs_: int, number_of_keyframe_pairs_: int):
        self.transp_interp_global_seq_id_bytes = Binary.read_bytes(model_, self.m2FromOfsTransp + M2Length.transp * self.transpIdFrom)

        number_of_ts_pairs_ofs = Binary.get_int_from_bytes(model_, self.m2FromOfsTransp + M2Length.transp * self.transpIdFrom + 8)
        number_of_kf_pairs_ofs = Binary.get_int_from_bytes(model_, self.m2FromOfsTransp + M2Length.transp * self.transpIdFrom + 16)

        for i in range(number_of_timestamp_pairs_):
            self.transp_ts_n_val.append(Binary.get_int_from_bytes(model_, number_of_ts_pairs_ofs + i * 8))
            self.transp_ts_ofs_val.append(Binary.get_int_from_bytes(model_, number_of_ts_pairs_ofs + i * 8 + 4))

        for i_ in range(number_of_keyframe_pairs_):
            self.transp_val_n_val.append(Binary.get_int_from_bytes(model_, number_of_kf_pairs_ofs + i_ * 8))
            self.transp_val_ofs_val.append(Binary.get_int_from_bytes(model_, number_of_kf_pairs_ofs + i_ * 8 + 4))

        for i2 in range(len(self.transp_ts_n_val)):
            self.transp_ts_seq_bytes.append(Binary.read_bytes(model_, self.transp_ts_ofs_val[i2], self.transp_ts_n_val[i2] * 4))

        for i2_ in range(len(self.transp_ts_n_val)):
            self.transp_val_seq_bytes.append(Binary.read_bytes(model_, self.transp_val_ofs_val[i2_], self.transp_val_n_val[i2_] * 2))

    def _transp_paste_transp(self, model_: BinaryIO, OfsTransp_: int, number_of_ts_pairs_: int, number_of_kf_pairs_: int):
        Binary.write_bytes(model_, OfsTransp_ + M2Length.transp * self.transpIdTo, self.transp_interp_global_seq_id_bytes)

        # numberOfTimestampPairs
        Binary.write_bytes(model_, OfsTransp_ + M2Length.transp * self.transpIdTo + 4, number_of_ts_pairs_.to_bytes(4, byteorder='little'))

        Binary.write_zeros(model_)

        last_offset1 = model_.seek(0, 2)
        Binary.write_bytes(model_, last_offset1, b'\x00\x00\x00\x00\x00\x00\x00\x00' * number_of_ts_pairs_)
        Binary.write_bytes(model_, OfsTransp_ + M2Length.transp * self.transpIdTo + 8, last_offset1.to_bytes(4, byteorder='little'))

        Binary.write_zeros(model_)

        # numberOfKeyFramePairs
        Binary.write_bytes(model_, OfsTransp_ + M2Length.transp * self.transpIdTo + 12, number_of_kf_pairs_.to_bytes(4, byteorder='little'))
        last_offset2 = model_.seek(0, 2)
        Binary.write_bytes(model_, last_offset2, b'\x00\x00\x00\x00\x00\x00\x00\x00' * number_of_kf_pairs_)
        Binary.write_bytes(model_, OfsTransp_ + M2Length.transp * self.transpIdTo + 16, last_offset2.to_bytes(4, byteorder='little'))

        Binary.write_zeros(model_)

        for i3 in range(number_of_ts_pairs_):  # Timestamps
            Binary.write_bytes(model_, last_offset1 + i3 * 8, self.transp_ts_n_val[i3].to_bytes(4, byteorder='little'))
            last_offset = model_.seek(0, 2)
            Binary.write_bytes(model_, last_offset1 + i3 * 8 + 4, last_offset.to_bytes(4, byteorder='little'))
            Binary.write_bytes(model_, last_offset, self.transp_ts_seq_bytes[i3])

        for i3_ in range(number_of_ts_pairs_):  # Values
            Binary.write_bytes(model_, last_offset2 + i3_ * 8, self.transp_val_n_val[i3_].to_bytes(4, byteorder='little'))
            last_offset_ = model_.seek(0, 2)
            Binary.write_bytes(model_, last_offset2 + i3_ * 8 + 4, last_offset_.to_bytes(4, byteorder='little'))
            Binary.write_bytes(model_, last_offset_, self.transp_val_seq_bytes[i3_])

        Binary.write_zeros(model_)


class TexAnimCloner(ParameterCloner):
    def __init__(self):
        super().__init__()
        self.texAnimIdFrom = None
        self.texAnimIdTo = None
        self.m2FromNTexAnim = 0
        self.m2ToNTexAnim = 0
        self.m2FromOfsTexAnim = 0
        self.m2ToOfsTexAnim = 0

        self.transl_interp_global_seq_id_bytes = None
        self.transl_ts_n_val = []
        self.transl_ts_ofs_val = []
        self.transl_ts_seq_bytes = []
        self.transl_val_n_val = []
        self.transl_val_ofs_val = []
        self.transl_val_seq_bytes = []

        self.rot_interp_global_seq_id_bytes = None
        self.rot_ts_n_val = []
        self.rot_ts_ofs_val = []
        self.rot_ts_seq_bytes = []
        self.rot_val_n_val = []
        self.rot_val_ofs_val = []
        self.rot_val_seq_bytes = []

        self.scal_interp_global_seq_id_bytes = None
        self.scal_ts_n_val = []
        self.scal_ts_ofs_val = []
        self.scal_ts_seq_bytes = []
        self.scal_val_n_val = []
        self.scal_val_ofs_val = []
        self.scal_val_seq_bytes = []

    def tex_anim_copy_pre(self):
        if not self._get_models_path():
            return

        try:
            tex_anim_id_from = int(dpg.get_value("inp_tex_anim_from"))
            tex_anim_id_to = int(dpg.get_value("inp_tex_anim_to"))
        except ValueError:
            StatusBar.error_info("ERROR: Texture animation ID must be integer.")
            return

        if self._check_id_match_error(name="texture animation", _id_from=tex_anim_id_from, _id_to=tex_anim_id_to):
            return

        self.texAnimIdFrom = tex_anim_id_from
        self.texAnimIdTo = tex_anim_id_to

        self.tex_anim_copy()

    def tex_anim_copy(self):
        if not self.isSameModel:
            with open(self.m2To, "rb+") as model_m2to:
                m2to_n_tex_anim = Binary.get_int_from_bytes(model_m2to, M2Offset.nTexAnims)
                if not m2to_n_tex_anim > 0:
                    StatusBar.error_info(f"ERROR: There are no texture animation in target model.")
                    return

                self.m2ToNTexAnim = m2to_n_tex_anim - 1
                self.m2ToOfsTexAnim = Binary.get_int_from_bytes(model_m2to, M2Offset.ofsTexAnims)

        with open(self.m2From, "rb+") as model_m2from:
            m2from_n_tex_anim = Binary.get_int_from_bytes(model_m2from, M2Offset.nTexAnims)
            if not m2from_n_tex_anim > 0:
                StatusBar.error_info(f"ERROR: There are no texture animation in model.")
                return

            self.m2FromNTexAnim = m2from_n_tex_anim - 1

            if self.isSameModel:
                self.m2ToNTexAnim = self.m2FromNTexAnim
                if self.texAnimIdFrom > self.m2FromNTexAnim or self.texAnimIdTo > self.m2FromNTexAnim:
                    StatusBar.error_info(f"ERROR: There is no such texture animation ID in the model.")
                    return

            if not self.isSameModel:
                if self.texAnimIdFrom > self.m2FromNTexAnim or self.texAnimIdTo > self.m2ToNTexAnim:
                    StatusBar.error_info(f"ERROR: There is no such texture animation ID in the model.")
                    return

            self.m2FromOfsTexAnim = Binary.get_int_from_bytes(model_m2from, M2Offset.ofsTexAnims)

            translation_n_ts_pairs = Binary.get_int_from_bytes(model_m2from,
                                                               self.m2FromOfsTexAnim + M2Length.texAnim * self.texAnimIdFrom + 4)
            translation_n_kf_pairs = Binary.get_int_from_bytes(model_m2from,
                                                               self.m2FromOfsTexAnim + M2Length.texAnim * self.texAnimIdFrom + 12)
            rotation_n_ts_pairs = Binary.get_int_from_bytes(model_m2from,
                                                            self.m2FromOfsTexAnim + M2Length.texAnim * self.texAnimIdFrom + 24)
            rotation_n_kf_pairs = Binary.get_int_from_bytes(model_m2from,
                                                            self.m2FromOfsTexAnim + M2Length.texAnim * self.texAnimIdFrom + 32)
            scaling_n_ts_pairs = Binary.get_int_from_bytes(model_m2from, self.m2FromOfsTexAnim + M2Length.texAnim * self.texAnimIdFrom + 44)
            scaling_n_kf_pairs = Binary.get_int_from_bytes(model_m2from, self.m2FromOfsTexAnim + M2Length.texAnim * self.texAnimIdFrom + 52)

            if (translation_n_ts_pairs < 1 and translation_n_kf_pairs < 1 and rotation_n_ts_pairs < 1 and
                    rotation_n_kf_pairs < 1 and scaling_n_ts_pairs < 1 and scaling_n_kf_pairs < 1):
                StatusBar.error_info(f"ERROR: Nothing to copy. Texture animation {self.texAnimIdFrom} is empty.")
                return

            # ? В зависимости от чекбоксов и наличия keyframes копируем и вставляем значения ----------------------------------------------
            if dpg.get_value("chk_tex_anim_cloner_Translation") and translation_n_ts_pairs > 0 and translation_n_kf_pairs > 0:
                self._tex_anim_copy_translation(model_m2from, translation_n_ts_pairs, translation_n_kf_pairs)
                if self.isSameModel:
                    self._tex_anim_paste_translation(model_m2from, self.m2FromOfsTexAnim, translation_n_ts_pairs, translation_n_kf_pairs)

            if dpg.get_value("chk_tex_anim_cloner_Rotation") and rotation_n_ts_pairs > 0 and rotation_n_kf_pairs > 0:
                self._tex_anim_copy_rotation(model_m2from, rotation_n_ts_pairs, rotation_n_kf_pairs)
                if self.isSameModel:
                    self._tex_anim_paste_rotation(model_m2from, self.m2FromOfsTexAnim, rotation_n_ts_pairs, rotation_n_kf_pairs)

            if dpg.get_value("chk_tex_anim_cloner_Scale") and scaling_n_ts_pairs > 0 and scaling_n_kf_pairs > 0:
                self._tex_anim_copy_scaling(model_m2from, scaling_n_ts_pairs, scaling_n_kf_pairs)
                if self.isSameModel:
                    self._tex_anim_paste_scaling(model_m2from, self.m2FromOfsTexAnim, scaling_n_ts_pairs, scaling_n_kf_pairs)

        # ? Если модели разные вставляем уже в другую модель ------------------------------------------------------------------------------
        if not self.isSameModel:
            with open(self.m2To, "rb+") as model_m2to:
                if dpg.get_value("chk_tex_anim_cloner_Translation") and translation_n_ts_pairs > 0 and translation_n_kf_pairs > 0:
                    self._tex_anim_paste_translation(model_m2to, self.m2ToOfsTexAnim, translation_n_ts_pairs, translation_n_kf_pairs)

                if dpg.get_value("chk_tex_anim_cloner_Rotation") and rotation_n_ts_pairs > 0 and rotation_n_kf_pairs > 0:
                    self._tex_anim_paste_rotation(model_m2to, self.m2ToOfsTexAnim, rotation_n_ts_pairs, rotation_n_kf_pairs)

                if dpg.get_value("chk_tex_anim_cloner_Scale") and scaling_n_ts_pairs > 0 and scaling_n_kf_pairs > 0:
                    self._tex_anim_paste_scaling(model_m2to, self.m2ToOfsTexAnim, scaling_n_ts_pairs, scaling_n_kf_pairs)

        StatusBar.success_info(f"Texture animation {self.texAnimIdFrom} -> {self.texAnimIdTo} copied successfully.")

    def _tex_anim_copy_translation(self, model_: BinaryIO, number_of_timestamp_pairs_: int, number_of_keyframe_pairs_: int):
        self.transl_interp_global_seq_id_bytes = Binary.read_bytes(model_,
                                                                   self.m2FromOfsTexAnim + M2Length.texAnim * self.texAnimIdFrom)

        number_of_ts_pairs_ofs = Binary.get_int_from_bytes(model_, self.m2FromOfsTexAnim + M2Length.texAnim * self.texAnimIdFrom + 8)
        number_of_kf_pairs_ofs = Binary.get_int_from_bytes(model_, self.m2FromOfsTexAnim + M2Length.texAnim * self.texAnimIdFrom + 16)

        for i in range(number_of_timestamp_pairs_):
            self.transl_ts_n_val.append(Binary.get_int_from_bytes(model_, number_of_ts_pairs_ofs + i * 8))
            self.transl_ts_ofs_val.append(Binary.get_int_from_bytes(model_, number_of_ts_pairs_ofs + i * 8 + 4))

        for i_ in range(number_of_keyframe_pairs_):
            self.transl_val_n_val.append(Binary.get_int_from_bytes(model_, number_of_kf_pairs_ofs + i_ * 8))
            self.transl_val_ofs_val.append(Binary.get_int_from_bytes(model_, number_of_kf_pairs_ofs + i_ * 8 + 4))

        for i2 in range(len(self.transl_ts_n_val)):
            self.transl_ts_seq_bytes.append(
                Binary.read_bytes(model_, self.transl_ts_ofs_val[i2], self.transl_ts_n_val[i2] * 4))

        for i2_ in range(len(self.transl_ts_n_val)):
            self.transl_val_seq_bytes.append(
                Binary.read_bytes(model_, self.transl_val_ofs_val[i2_], self.transl_val_n_val[i2_] * 12))

    def _tex_anim_paste_translation(self, model_: BinaryIO, OfsTexAnim_: int, number_of_ts_pairs_: int, number_of_kf_pairs_: int):
        Binary.write_bytes(model_, OfsTexAnim_ + M2Length.texAnim * self.texAnimIdTo, self.transl_interp_global_seq_id_bytes)

        # numberOfTimestampPairs
        Binary.write_bytes(model_, OfsTexAnim_ + M2Length.texAnim * self.texAnimIdTo + 4,
                           number_of_ts_pairs_.to_bytes(4, byteorder='little'))

        Binary.write_zeros(model_)

        last_offset1 = model_.seek(0, 2)
        Binary.write_bytes(model_, last_offset1, b'\x00\x00\x00\x00\x00\x00\x00\x00' * number_of_ts_pairs_)
        Binary.write_bytes(model_, OfsTexAnim_ + M2Length.texAnim * self.texAnimIdTo + 8, last_offset1.to_bytes(4, byteorder='little'))

        Binary.write_zeros(model_)

        # numberOfKeyFramePairs
        Binary.write_bytes(model_, OfsTexAnim_ + M2Length.texAnim * self.texAnimIdTo + 12,
                           number_of_kf_pairs_.to_bytes(4, byteorder='little'))
        last_offset2 = model_.seek(0, 2)
        Binary.write_bytes(model_, last_offset2, b'\x00\x00\x00\x00\x00\x00\x00\x00' * number_of_kf_pairs_)
        Binary.write_bytes(model_, OfsTexAnim_ + M2Length.texAnim * self.texAnimIdTo + 16, last_offset2.to_bytes(4, byteorder='little'))

        Binary.write_zeros(model_)

        for i3 in range(number_of_ts_pairs_):  # Timestamps
            Binary.write_bytes(model_, last_offset1 + i3 * 8, self.transl_ts_n_val[i3].to_bytes(4, byteorder='little'))
            last_offset = model_.seek(0, 2)
            Binary.write_bytes(model_, last_offset1 + i3 * 8 + 4, last_offset.to_bytes(4, byteorder='little'))
            Binary.write_bytes(model_, last_offset, self.transl_ts_seq_bytes[i3])

        for i3_ in range(number_of_ts_pairs_):  # Values
            Binary.write_bytes(model_, last_offset2 + i3_ * 8, self.transl_val_n_val[i3_].to_bytes(4, byteorder='little'))
            last_offset_ = model_.seek(0, 2)
            Binary.write_bytes(model_, last_offset2 + i3_ * 8 + 4, last_offset_.to_bytes(4, byteorder='little'))
            Binary.write_bytes(model_, last_offset_, self.transl_val_seq_bytes[i3_])

        Binary.write_zeros(model_)

    def _tex_anim_copy_rotation(self, model_: BinaryIO, number_of_timestamp_pairs_: int, number_of_keyframe_pairs_: int):
        self.rot_interp_global_seq_id_bytes = Binary.read_bytes(model_,
                                                                self.m2FromOfsTexAnim + M2Length.texAnim * self.texAnimIdFrom + 20)

        number_of_ts_pairs_ofs = Binary.get_int_from_bytes(model_, self.m2FromOfsTexAnim + M2Length.texAnim * self.texAnimIdFrom + 28)
        number_of_kf_pairs_ofs = Binary.get_int_from_bytes(model_, self.m2FromOfsTexAnim + M2Length.texAnim * self.texAnimIdFrom + 36)

        for i in range(number_of_timestamp_pairs_):
            self.rot_ts_n_val.append(Binary.get_int_from_bytes(model_, number_of_ts_pairs_ofs + i * 8))
            self.rot_ts_ofs_val.append(Binary.get_int_from_bytes(model_, number_of_ts_pairs_ofs + i * 8 + 4))

        for i_ in range(number_of_keyframe_pairs_):
            self.rot_val_n_val.append(Binary.get_int_from_bytes(model_, number_of_kf_pairs_ofs + i_ * 8))
            self.rot_val_ofs_val.append(Binary.get_int_from_bytes(model_, number_of_kf_pairs_ofs + i_ * 8 + 4))

        for i2 in range(len(self.rot_ts_n_val)):
            self.rot_ts_seq_bytes.append(Binary.read_bytes(model_, self.rot_ts_ofs_val[i2], self.rot_ts_n_val[i2] * 4))

        for i2_ in range(len(self.rot_ts_n_val)):
            self.rot_val_seq_bytes.append(Binary.read_bytes(model_, self.rot_val_ofs_val[i2_], self.rot_val_n_val[i2_] * 8))

    def _tex_anim_paste_rotation(self, model_: BinaryIO, OfsTexAnim_: int, number_of_ts_pairs_: int, number_of_kf_pairs_: int):
        Binary.write_bytes(model_, OfsTexAnim_ + M2Length.texAnim * self.texAnimIdTo + 20, self.rot_interp_global_seq_id_bytes)

        # numberOfTimestampPairs
        Binary.write_bytes(model_, OfsTexAnim_ + M2Length.texAnim * self.texAnimIdTo + 24,
                           number_of_ts_pairs_.to_bytes(4, byteorder='little'))

        Binary.write_zeros(model_)

        last_offset1 = model_.seek(0, 2)
        Binary.write_bytes(model_, last_offset1, b'\x00\x00\x00\x00\x00\x00\x00\x00' * number_of_ts_pairs_)
        Binary.write_bytes(model_, OfsTexAnim_ + M2Length.texAnim * self.texAnimIdTo + 28, last_offset1.to_bytes(4, byteorder='little'))

        Binary.write_zeros(model_)

        # numberOfKeyFramePairs
        Binary.write_bytes(model_, OfsTexAnim_ + M2Length.texAnim * self.texAnimIdTo + 32,
                           number_of_kf_pairs_.to_bytes(4, byteorder='little'))
        last_offset2 = model_.seek(0, 2)
        Binary.write_bytes(model_, last_offset2, b'\x00\x00\x00\x00\x00\x00\x00\x00' * number_of_kf_pairs_)
        Binary.write_bytes(model_, OfsTexAnim_ + M2Length.texAnim * self.texAnimIdTo + 36, last_offset2.to_bytes(4, byteorder='little'))

        Binary.write_zeros(model_)

        for i3 in range(number_of_ts_pairs_):  # Timestamps
            Binary.write_bytes(model_, last_offset1 + i3 * 8, self.rot_ts_n_val[i3].to_bytes(4, byteorder='little'))
            last_offset = model_.seek(0, 2)
            Binary.write_bytes(model_, last_offset1 + i3 * 8 + 4, last_offset.to_bytes(4, byteorder='little'))
            Binary.write_bytes(model_, last_offset, self.rot_ts_seq_bytes[i3])

        for i3_ in range(number_of_ts_pairs_):  # Values
            Binary.write_bytes(model_, last_offset2 + i3_ * 8, self.rot_val_n_val[i3_].to_bytes(4, byteorder='little'))
            last_offset_ = model_.seek(0, 2)
            Binary.write_bytes(model_, last_offset2 + i3_ * 8 + 4, last_offset_.to_bytes(4, byteorder='little'))
            Binary.write_bytes(model_, last_offset_, self.rot_val_seq_bytes[i3_])

        Binary.write_zeros(model_)

    def _tex_anim_copy_scaling(self, model_: BinaryIO, number_of_ts_pairs_: int, number_of_kf_pairs_: int):
        self.scal_interp_global_seq_id_bytes = Binary.read_bytes(model_,
                                                                 self.m2FromOfsTexAnim + M2Length.texAnim * self.texAnimIdFrom + 40)

        number_of_ts_pairs_ofs = Binary.get_int_from_bytes(model_, self.m2FromOfsTexAnim + M2Length.texAnim * self.texAnimIdFrom + 48)
        number_of_kf_pairs_ofs = Binary.get_int_from_bytes(model_, self.m2FromOfsTexAnim + M2Length.texAnim * self.texAnimIdFrom + 56)

        for i in range(number_of_ts_pairs_):
            self.scal_ts_n_val.append(Binary.get_int_from_bytes(model_, number_of_ts_pairs_ofs + i * 8))
            self.scal_ts_ofs_val.append(Binary.get_int_from_bytes(model_, number_of_ts_pairs_ofs + i * 8 + 4))

        for i_ in range(number_of_kf_pairs_):
            self.scal_val_n_val.append(Binary.get_int_from_bytes(model_, number_of_kf_pairs_ofs + i_ * 8))
            self.scal_val_ofs_val.append(Binary.get_int_from_bytes(model_, number_of_kf_pairs_ofs + i_ * 8 + 4))

        for i2 in range(len(self.scal_ts_n_val)):
            self.scal_ts_seq_bytes.append(Binary.read_bytes(model_, self.scal_ts_ofs_val[i2], self.scal_ts_n_val[i2] * 4))

        for i2_ in range(len(self.scal_ts_n_val)):
            self.scal_val_seq_bytes.append(Binary.read_bytes(model_, self.scal_val_ofs_val[i2_], self.scal_val_n_val[i2_] * 12))

    def _tex_anim_paste_scaling(self, model_: BinaryIO, OfsTexAnim_: int, number_of_ts_pairs_: int, number_of_kf_pairs_: int):
        Binary.write_bytes(model_, OfsTexAnim_ + M2Length.texAnim * self.texAnimIdTo + 40, self.scal_interp_global_seq_id_bytes)

        # numberOfTimestampPairs
        Binary.write_bytes(model_, OfsTexAnim_ + M2Length.texAnim * self.texAnimIdTo + 44,
                           number_of_ts_pairs_.to_bytes(4, byteorder='little'))

        Binary.write_zeros(model_)

        last_offset1 = model_.seek(0, 2)
        Binary.write_bytes(model_, last_offset1, b'\x00\x00\x00\x00\x00\x00\x00\x00' * number_of_ts_pairs_)
        Binary.write_bytes(model_, OfsTexAnim_ + M2Length.texAnim * self.texAnimIdTo + 48, last_offset1.to_bytes(4, byteorder='little'))

        Binary.write_zeros(model_)

        # numberOfKeyFramePairs
        Binary.write_bytes(model_, OfsTexAnim_ + M2Length.texAnim * self.texAnimIdTo + 52,
                           number_of_kf_pairs_.to_bytes(4, byteorder='little'))
        last_offset2 = model_.seek(0, 2)
        Binary.write_bytes(model_, last_offset2, b'\x00\x00\x00\x00\x00\x00\x00\x00' * number_of_kf_pairs_)
        Binary.write_bytes(model_, OfsTexAnim_ + M2Length.texAnim * self.texAnimIdTo + 56, last_offset2.to_bytes(4, byteorder='little'))

        Binary.write_zeros(model_)

        for i3 in range(number_of_ts_pairs_):  # Timestamps
            Binary.write_bytes(model_, last_offset1 + i3 * 8, self.scal_ts_n_val[i3].to_bytes(4, byteorder='little'))
            last_offset = model_.seek(0, 2)
            Binary.write_bytes(model_, last_offset1 + i3 * 8 + 4, last_offset.to_bytes(4, byteorder='little'))
            Binary.write_bytes(model_, last_offset, self.scal_ts_seq_bytes[i3])

        for i3_ in range(number_of_ts_pairs_):  # Values
            Binary.write_bytes(model_, last_offset2 + i3_ * 8, self.scal_val_n_val[i3_].to_bytes(4, byteorder='little'))
            last_offset_ = model_.seek(0, 2)
            Binary.write_bytes(model_, last_offset2 + i3_ * 8 + 4, last_offset_.to_bytes(4, byteorder='little'))
            Binary.write_bytes(model_, last_offset_, self.scal_val_seq_bytes[i3_])

        Binary.write_zeros(model_)


def bone_cloner_init():
    StatusBar.clear_info()
    bone_cloner = BoneCloner()
    bone_cloner.bone_copy_pre()


def color_cloner_init():
    StatusBar.clear_info()
    color_cloner = ColorCloner()
    color_cloner.color_copy_pre()


def transparency_cloner_init():
    StatusBar.clear_info()
    transparency_cloner = TransparencyCloner()
    transparency_cloner.transp_copy_pre()


def tex_anim_cloner_init():
    StatusBar.clear_info()
    tex_anim_cloner = TexAnimCloner()
    tex_anim_cloner.tex_anim_copy_pre()
