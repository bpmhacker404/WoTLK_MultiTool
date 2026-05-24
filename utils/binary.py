from typing import BinaryIO


class Binary:
    @staticmethod
    def get_int_from_bytes(file: BinaryIO, offset: int, length: int = 4) -> int:
        file.seek(offset)
        some_bytes = file.read(length)
        return int.from_bytes(some_bytes, 'little')

    @staticmethod
    def get_int_and_bytes(file: BinaryIO, offset: int, length: int = 4) -> tuple[int, bytes]:
        file.seek(offset)
        some_bytes = file.read(length)
        return int.from_bytes(some_bytes, 'little'), some_bytes

    @staticmethod
    def read_bytes(model: BinaryIO, offset: int, length: int = 4) -> bytes:
        model.seek(offset)
        return model.read(length)

    @staticmethod
    def set_int_to_bytes(file: BinaryIO, offset: int, n: int, length: int = 4):
        file.seek(offset)
        file.write(n.to_bytes(length, 'little'))

    @staticmethod
    def write_bytes(model: BinaryIO, offset: int, bytes_: bytes):
        model.seek(offset)
        model.write(bytes_)

    @staticmethod
    def write_offset(model: BinaryIO) -> tuple[int, bytes]:
        last_offset = model.seek(0, 2)
        model.write(b'\x00' * 8)
        last_offset_bytes = last_offset.to_bytes(4, byteorder='little')
        return last_offset, last_offset_bytes

    @staticmethod
    def write_seq_offset(model: BinaryIO, n_keyframes: int, value_bytes: bytes = b'\x00\x00\x00\x00') -> bytes:
        last_offset = model.seek(0, 2)
        model.write(value_bytes * n_keyframes)
        last_offset_bytes = last_offset.to_bytes(4, byteorder='little')
        return last_offset_bytes

    @staticmethod
    def write_to_end(model: BinaryIO, bytes_: bytes) -> int:
        last_offset = model.seek(0, 2)
        model.write(bytes_)
        return last_offset

    @staticmethod
    def write_zeros(model: BinaryIO):
        last_byte = model.seek(0, 2)
        deficient_bytes_for_end = 16 - last_byte % 16
        model.write(b'\x00' * deficient_bytes_for_end)
