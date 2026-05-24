from typing import BinaryIO

import dearpygui.dearpygui as dpg
import os

from utils.binary import Binary
from utils.offsets import M2Offsets, M2Lengths
from utils.statusbar import StatusBar


class ParameterCloner:
    def __init__(self):
        self.m2From = None
        self.m2To = None
        self.boneIdFrom = None
        self.boneIdTo = None
        self.m2FromNBones = 0
        self.m2ToNBones = 0
        self.m2FromOfsBones = 0

    def bone_copy_pre(self):
        m2from_path = dpg.get_value("inp_model")
        try:
            bone_id_from = int(dpg.get_value("inp_bone_from"))
            bone_id_to = int(dpg.get_value("inp_bone_to"))
        except ValueError:
            StatusBar.error_info("ERROR: Bone ID must be integer.")
            return

        if not m2from_path:
            StatusBar.error_info("ERROR: Select the source model.")
            return
        if not os.path.exists(m2from_path):
            StatusBar.error_info(f"{os.path.basename(m2from_path)} not found.")
            return
        if bone_id_from == bone_id_to:
            StatusBar.error_info("ERROR: the bone IDs cannot match.")
            return

        self.m2From = m2from_path
        self.boneIdFrom = bone_id_from
        self.boneIdTo = bone_id_to

        self.bone_copy()

    def bone_copy(self):
        with open(self.m2From, "rb+") as model_m2from:
            m2_from_n_bones = Binary.get_int_from_bytes(model_m2from, M2Offsets.nBones)
            if not m2_from_n_bones > 0:
                StatusBar.error_info(f"ERROR: There are no bones in model.")
                return

            self.m2FromNBones = m2_from_n_bones

            if self.boneIdFrom > self.m2FromNBones or self.boneIdTo > self.m2FromNBones:
                StatusBar.error_info(f"ERROR: There is no such bone ID in the model.")
                return

            self.m2FromOfsBones = Binary.get_int_from_bytes(model_m2from, M2Offsets.ofsBones)

            translation_n_timestamp_pairs = Binary.get_int_from_bytes(model_m2from,
                                                                      self.m2FromOfsBones + M2Lengths.bone * self.boneIdFrom + 20)
            translation_n_keyframe_pairs = Binary.get_int_from_bytes(model_m2from,
                                                                     self.m2FromOfsBones + M2Lengths.bone * self.boneIdFrom + 28)
            rotation_n_timestamp_pairs = Binary.get_int_from_bytes(model_m2from,
                                                                   self.m2FromOfsBones + M2Lengths.bone * self.boneIdFrom + 40)
            rotation_n_keyframe_pairs = Binary.get_int_from_bytes(model_m2from,
                                                                  self.m2FromOfsBones + M2Lengths.bone * self.boneIdFrom + 48)
            scaling_n_timestamp_pairs = Binary.get_int_from_bytes(model_m2from,
                                                                  self.m2FromOfsBones + M2Lengths.bone * self.boneIdFrom + 60)
            scaling_n_keyframe_pairs = Binary.get_int_from_bytes(model_m2from,
                                                                 self.m2FromOfsBones + M2Lengths.bone * self.boneIdFrom + 68)

            if (translation_n_timestamp_pairs < 1 and translation_n_keyframe_pairs < 1 and rotation_n_timestamp_pairs < 1 and
                    rotation_n_keyframe_pairs < 1 and scaling_n_timestamp_pairs < 1 and scaling_n_keyframe_pairs < 1):
                StatusBar.error_info(f"ERROR: Nothing to copy. Bone {self.boneIdFrom} is empty.")
                return

            if translation_n_timestamp_pairs > 0 and translation_n_keyframe_pairs > 0:
                self.bone_copy_translation(model_m2from, translation_n_timestamp_pairs, translation_n_keyframe_pairs)
            if rotation_n_timestamp_pairs > 0 and rotation_n_keyframe_pairs > 0:
                self.bone_copy_rotation(model_m2from, rotation_n_timestamp_pairs, rotation_n_keyframe_pairs)
            if scaling_n_timestamp_pairs > 0 and scaling_n_keyframe_pairs > 0:
                self.bone_copy_scaling(model_m2from, scaling_n_timestamp_pairs, scaling_n_keyframe_pairs)

            pivot_point_bytes = Binary.read_bytes(model_m2from, self.m2FromOfsBones + M2Lengths.bone * self.boneIdFrom + 76, length=12)
            Binary.write_bytes(model_m2from, self.m2FromOfsBones + M2Lengths.bone * self.boneIdTo + 76, pivot_point_bytes)

        StatusBar.success_info("Copied successfully.")

    def bone_copy_translation(self, model_: BinaryIO, number_of_timestamp_pairs_: int, number_of_keyframe_pairs_: int):
        timestamps_n_values = []
        timestamps_ofs_values = []
        timestamps_sequences_bytes = []
        values_n_values = []
        values_ofs_values = []
        values_sequences_bytes = []

        # * Копируем значения
        interpolation_global_seq_id_bytes = Binary.read_bytes(model_, self.m2FromOfsBones + M2Lengths.bone * self.boneIdFrom + 16)

        number_of_timestamp_pairs_ofs = Binary.get_int_from_bytes(model_,
                                                                  self.m2FromOfsBones + M2Lengths.bone * self.boneIdFrom + 24)
        number_of_keyframe_pairs_ofs = Binary.get_int_from_bytes(model_,
                                                                 self.m2FromOfsBones + M2Lengths.bone * self.boneIdFrom + 32)

        for i in range(number_of_timestamp_pairs_):
            timestamps_n_values.append(Binary.get_int_from_bytes(model_, number_of_timestamp_pairs_ofs + i * 8))
            timestamps_ofs_values.append(Binary.get_int_from_bytes(model_, number_of_timestamp_pairs_ofs + i * 8 + 4))

        for i_ in range(number_of_keyframe_pairs_):
            values_n_values.append(Binary.get_int_from_bytes(model_, number_of_keyframe_pairs_ofs + i_ * 8))
            values_ofs_values.append(Binary.get_int_from_bytes(model_, number_of_keyframe_pairs_ofs + i_ * 8 + 4))

        for i2 in range(len(timestamps_n_values)):
            timestamps_sequences_bytes.append(Binary.read_bytes(model_, timestamps_ofs_values[i2], timestamps_n_values[i2] * 4))

        for i2_ in range(len(timestamps_n_values)):
            values_sequences_bytes.append(Binary.read_bytes(model_, values_ofs_values[i2_], values_n_values[i2_] * 12))

        # * Вставляем значения в целевую кость
        Binary.write_bytes(model_, self.m2FromOfsBones + M2Lengths.bone * self.boneIdTo + 16, interpolation_global_seq_id_bytes)

        # numberOfTimestampPairs
        Binary.write_bytes(model_, self.m2FromOfsBones + M2Lengths.bone * self.boneIdTo + 20,
                           number_of_timestamp_pairs_.to_bytes(4, byteorder='little'))

        Binary.write_zeros(model_)

        last_offset1 = model_.seek(0, 2)
        Binary.write_bytes(model_, last_offset1, b'\x00\x00\x00\x00\x00\x00\x00\x00' * number_of_timestamp_pairs_)
        Binary.write_bytes(model_, self.m2FromOfsBones + M2Lengths.bone * self.boneIdTo + 24,
                           last_offset1.to_bytes(4, byteorder='little'))

        Binary.write_zeros(model_)

        # numberOfKeyFramePairs
        Binary.write_bytes(model_, self.m2FromOfsBones + M2Lengths.bone * self.boneIdTo + 28,
                           number_of_keyframe_pairs_.to_bytes(4, byteorder='little'))
        last_offset2 = model_.seek(0, 2)
        Binary.write_bytes(model_, last_offset2, b'\x00\x00\x00\x00\x00\x00\x00\x00' * number_of_keyframe_pairs_)
        Binary.write_bytes(model_, self.m2FromOfsBones + M2Lengths.bone * self.boneIdTo + 32,
                           last_offset2.to_bytes(4, byteorder='little'))

        Binary.write_zeros(model_)

        # Timestamps
        for i3 in range(number_of_timestamp_pairs_):
            Binary.write_bytes(model_, last_offset1 + i3 * 8, timestamps_n_values[i3].to_bytes(4, byteorder='little'))
            last_offset = model_.seek(0, 2)
            Binary.write_bytes(model_, last_offset1 + i3 * 8 + 4, last_offset.to_bytes(4, byteorder='little'))
            Binary.write_bytes(model_, last_offset, timestamps_sequences_bytes[i3])

        # Values
        for i3_ in range(number_of_timestamp_pairs_):
            Binary.write_bytes(model_, last_offset2 + i3_ * 8, values_n_values[i3_].to_bytes(4, byteorder='little'))
            last_offset_ = model_.seek(0, 2)
            Binary.write_bytes(model_, last_offset2 + i3_ * 8 + 4, last_offset_.to_bytes(4, byteorder='little'))
            Binary.write_bytes(model_, last_offset_, values_sequences_bytes[i3_])

        Binary.write_zeros(model_)

    def bone_copy_rotation(self, model_: BinaryIO, number_of_timestamp_pairs_: int, number_of_keyframe_pairs_: int):
        timestamps_n_values = []
        timestamps_ofs_values = []
        timestamps_sequences_bytes = []
        values_n_values = []
        values_ofs_values = []
        values_sequences_bytes = []

        # * Копируем значения
        interpolation_global_seq_id_bytes = Binary.read_bytes(model_, self.m2FromOfsBones + M2Lengths.bone * self.boneIdFrom + 36)

        number_of_timestamp_pairs_ofs = Binary.get_int_from_bytes(model_,
                                                                  self.m2FromOfsBones + M2Lengths.bone * self.boneIdFrom + 44)
        number_of_keyframe_pairs_ofs = Binary.get_int_from_bytes(model_,
                                                                 self.m2FromOfsBones + M2Lengths.bone * self.boneIdFrom + 52)

        for i in range(number_of_timestamp_pairs_):
            timestamps_n_values.append(Binary.get_int_from_bytes(model_, number_of_timestamp_pairs_ofs + i * 8))
            timestamps_ofs_values.append(Binary.get_int_from_bytes(model_, number_of_timestamp_pairs_ofs + i * 8 + 4))

        for i_ in range(number_of_keyframe_pairs_):
            values_n_values.append(Binary.get_int_from_bytes(model_, number_of_keyframe_pairs_ofs + i_ * 8))
            values_ofs_values.append(Binary.get_int_from_bytes(model_, number_of_keyframe_pairs_ofs + i_ * 8 + 4))

        for i2 in range(len(timestamps_n_values)):
            timestamps_sequences_bytes.append(Binary.read_bytes(model_, timestamps_ofs_values[i2], timestamps_n_values[i2] * 4))

        for i2_ in range(len(timestamps_n_values)):
            values_sequences_bytes.append(Binary.read_bytes(model_, values_ofs_values[i2_], values_n_values[i2_] * 8))

        # * Вставляем значения в целевую кость
        Binary.write_bytes(model_, self.m2FromOfsBones + M2Lengths.bone * self.boneIdTo + 36, interpolation_global_seq_id_bytes)

        # numberOfTimestampPairs
        Binary.write_bytes(model_, self.m2FromOfsBones + M2Lengths.bone * self.boneIdTo + 40,
                           number_of_timestamp_pairs_.to_bytes(4, byteorder='little'))

        Binary.write_zeros(model_)

        last_offset1 = model_.seek(0, 2)
        Binary.write_bytes(model_, last_offset1, b'\x00\x00\x00\x00\x00\x00\x00\x00' * number_of_timestamp_pairs_)
        Binary.write_bytes(model_, self.m2FromOfsBones + M2Lengths.bone * self.boneIdTo + 44,
                           last_offset1.to_bytes(4, byteorder='little'))

        Binary.write_zeros(model_)

        # numberOfKeyFramePairs
        Binary.write_bytes(model_, self.m2FromOfsBones + M2Lengths.bone * self.boneIdTo + 48,
                           number_of_keyframe_pairs_.to_bytes(4, byteorder='little'))
        last_offset2 = model_.seek(0, 2)
        Binary.write_bytes(model_, last_offset2, b'\x00\x00\x00\x00\x00\x00\x00\x00' * number_of_keyframe_pairs_)
        Binary.write_bytes(model_, self.m2FromOfsBones + M2Lengths.bone * self.boneIdTo + 52,
                           last_offset2.to_bytes(4, byteorder='little'))

        Binary.write_zeros(model_)

        # Timestamps
        for i3 in range(number_of_timestamp_pairs_):
            Binary.write_bytes(model_, last_offset1 + i3 * 8, timestamps_n_values[i3].to_bytes(4, byteorder='little'))
            last_offset = model_.seek(0, 2)
            Binary.write_bytes(model_, last_offset1 + i3 * 8 + 4, last_offset.to_bytes(4, byteorder='little'))
            Binary.write_bytes(model_, last_offset, timestamps_sequences_bytes[i3])

        # Values
        for i3_ in range(number_of_timestamp_pairs_):
            Binary.write_bytes(model_, last_offset2 + i3_ * 8, values_n_values[i3_].to_bytes(4, byteorder='little'))
            last_offset_ = model_.seek(0, 2)
            Binary.write_bytes(model_, last_offset2 + i3_ * 8 + 4, last_offset_.to_bytes(4, byteorder='little'))
            Binary.write_bytes(model_, last_offset_, values_sequences_bytes[i3_])

        Binary.write_zeros(model_)

    def bone_copy_scaling(self, model_: BinaryIO, number_of_timestamp_pairs_: int, number_of_keyframe_pairs_: int):
        timestamps_n_values = []
        timestamps_ofs_values = []
        timestamps_sequences_bytes = []
        values_n_values = []
        values_ofs_values = []
        values_sequences_bytes = []

        # * Копируем значения
        interpolation_global_seq_id_bytes = Binary.read_bytes(model_, self.m2FromOfsBones + M2Lengths.bone * self.boneIdFrom + 56)

        number_of_timestamp_pairs_ofs = Binary.get_int_from_bytes(model_,
                                                                  self.m2FromOfsBones + M2Lengths.bone * self.boneIdFrom + 64)
        number_of_keyframe_pairs_ofs = Binary.get_int_from_bytes(model_,
                                                                 self.m2FromOfsBones + M2Lengths.bone * self.boneIdFrom + 72)

        for i in range(number_of_timestamp_pairs_):
            timestamps_n_values.append(Binary.get_int_from_bytes(model_, number_of_timestamp_pairs_ofs + i * 8))
            timestamps_ofs_values.append(Binary.get_int_from_bytes(model_, number_of_timestamp_pairs_ofs + i * 8 + 4))

        for i_ in range(number_of_keyframe_pairs_):
            values_n_values.append(Binary.get_int_from_bytes(model_, number_of_keyframe_pairs_ofs + i_ * 8))
            values_ofs_values.append(Binary.get_int_from_bytes(model_, number_of_keyframe_pairs_ofs + i_ * 8 + 4))

        for i2 in range(len(timestamps_n_values)):
            timestamps_sequences_bytes.append(Binary.read_bytes(model_, timestamps_ofs_values[i2], timestamps_n_values[i2] * 4))

        for i2_ in range(len(timestamps_n_values)):
            values_sequences_bytes.append(Binary.read_bytes(model_, values_ofs_values[i2_], values_n_values[i2_] * 12))

        # * Вставляем значения в целевую кость
        Binary.write_bytes(model_, self.m2FromOfsBones + M2Lengths.bone * self.boneIdTo + 56, interpolation_global_seq_id_bytes)

        # numberOfTimestampPairs
        Binary.write_bytes(model_, self.m2FromOfsBones + M2Lengths.bone * self.boneIdTo + 60,
                           number_of_timestamp_pairs_.to_bytes(4, byteorder='little'))

        Binary.write_zeros(model_)

        last_offset1 = model_.seek(0, 2)
        Binary.write_bytes(model_, last_offset1, b'\x00\x00\x00\x00\x00\x00\x00\x00' * number_of_timestamp_pairs_)
        Binary.write_bytes(model_, self.m2FromOfsBones + M2Lengths.bone * self.boneIdTo + 64,
                           last_offset1.to_bytes(4, byteorder='little'))

        Binary.write_zeros(model_)

        # numberOfKeyFramePairs
        Binary.write_bytes(model_, self.m2FromOfsBones + M2Lengths.bone * self.boneIdTo + 68,
                           number_of_keyframe_pairs_.to_bytes(4, byteorder='little'))
        last_offset2 = model_.seek(0, 2)
        Binary.write_bytes(model_, last_offset2, b'\x00\x00\x00\x00\x00\x00\x00\x00' * number_of_keyframe_pairs_)
        Binary.write_bytes(model_, self.m2FromOfsBones + M2Lengths.bone * self.boneIdTo + 72,
                           last_offset2.to_bytes(4, byteorder='little'))

        Binary.write_zeros(model_)

        # Timestamps
        for i3 in range(number_of_timestamp_pairs_):
            Binary.write_bytes(model_, last_offset1 + i3 * 8, timestamps_n_values[i3].to_bytes(4, byteorder='little'))
            last_offset = model_.seek(0, 2)
            Binary.write_bytes(model_, last_offset1 + i3 * 8 + 4, last_offset.to_bytes(4, byteorder='little'))
            Binary.write_bytes(model_, last_offset, timestamps_sequences_bytes[i3])

        # Values
        for i3_ in range(number_of_timestamp_pairs_):
            Binary.write_bytes(model_, last_offset2 + i3_ * 8, values_n_values[i3_].to_bytes(4, byteorder='little'))
            last_offset_ = model_.seek(0, 2)
            Binary.write_bytes(model_, last_offset2 + i3_ * 8 + 4, last_offset_.to_bytes(4, byteorder='little'))
            Binary.write_bytes(model_, last_offset_, values_sequences_bytes[i3_])

        Binary.write_zeros(model_)


def parameter_cloner_init():
    StatusBar.clear_info()
    parameter_cloner = ParameterCloner()
    parameter_cloner.bone_copy_pre()
