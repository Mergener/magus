from io import BytesIO

class ByteReader:
    def __init__(self, data: bytes | BytesIO = BytesIO()):
        if isinstance(data, bytes):
            data = BytesIO(data)
        self._stream = data
        
    def read_int8(self) -> int:
        return int.from_bytes(self._stream.read(1), byteorder='little', signed=True)

    def read_int16(self) -> int:
        return int.from_bytes(self._stream.read(2), byteorder='little', signed=True)

    def read_int32(self) -> int:
        return int.from_bytes(self._stream.read(4), byteorder='little', signed=True)

    def read_int64(self) -> int:
        return int.from_bytes(self._stream.read(8), byteorder='little', signed=True)

    def read_str(self) -> str:
        n = self.read_int16()
        return self._stream.read(n).decode()

    def read_uint8(self) -> int:
        return int.from_bytes(self._stream.read(1), byteorder='little', signed=False)

    def read_uint16(self) -> int:
        return int.from_bytes(self._stream.read(2), byteorder='little', signed=False)

    def read_uint32(self) -> int:
        return int.from_bytes(self._stream.read(4), byteorder='little', signed=False)

    def read_uint64(self) -> int:
        return int.from_bytes(self._stream.read(8), byteorder='little', signed=False)

    def data(self):
        return self._stream.getvalue()

class ByteWriter:
    def __init__(self, data: bytes | BytesIO = BytesIO()):
        if isinstance(data, bytes):
            data = BytesIO(data)
        self._stream = data

    def write_int8(self, i: int):
        self._stream.write(i.to_bytes(1, byteorder='little', signed=True))

    def write_int16(self, i: int):
        self._stream.write(i.to_bytes(2, byteorder='little', signed=True))

    def write_int32(self, i: int):
        self._stream.write(i.to_bytes(4, byteorder='little', signed=True))

    def write_int64(self, i: int):
        self._stream.write(i.to_bytes(8, byteorder='little', signed=True))

    def write_str(self, s: str):
        encoded = s.encode()
        self.write_int16(len(encoded))
        self._stream.write(encoded)

    def write_uint8(self, i: int):
        self._stream.write(i.to_bytes(1, byteorder='little', signed=False))

    def write_uint16(self, i: int):
        self._stream.write(i.to_bytes(2, byteorder='little', signed=False))

    def write_uint32(self, i: int):
        self._stream.write(i.to_bytes(4, byteorder='little', signed=False))

    def write_uint64(self, i: int):
        self._stream.write(i.to_bytes(8, byteorder='little', signed=False))

    def data(self):
        return self._stream.getvalue()
