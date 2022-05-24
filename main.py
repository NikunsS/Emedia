from src.png import PNG
from src.chunk import Chunk
import matplotlib.pyplot as plt


# initialize png to store all data
png = PNG()


def extract_data_from_chunk(file):
    length = file.read(4)
    if not length:
        return False
    t = file.read(4)
    data = file.read(int.from_bytes(length, byteorder='big'))
    crc = file.read(4)

    return Chunk(length, t, data, crc)

filename = input('Enter file name: ')
with open(filename, 'rb') as f:
    b = f.read(8)

    if b == png.first_eight_bytes:
        print('This is a PNG file!')

    while True:
        if c := extract_data_from_chunk(f):
            png.chunks.append(c)
        else:
            break
        
png.read_data()
png.show_IDAT_image()
png.show_spectrum()
plt.show()
png.delete_ancillary_chunks()
png.show_write_new_img()