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
        return f'Chunk {self.type} of length {int.from_bytes(self.length, "big")},'\
                + f' crc: {self.crc}'
    
    def get_length(self):
        return int.from_bytes(self.length, 'big')