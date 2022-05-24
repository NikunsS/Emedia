"""
Class representing chunk in a PNG file format
"""


class Chunk:
    def __init__(self, length, type, data, crc):
        self.length = length
        self.type = type
        self.data = data
        self.crc = crc

    def __str__(self):
        return f'Chunk {self.type} of length {self.length}, data: {self.data}'\
                + f' crc: {self.crc}'