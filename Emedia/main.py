from src.png import PNG
from src.chunk import Chunk
from src.rsa import RSA
import matplotlib.pyplot as plt
import time

img_name = "dice.png"

def extract_data_from_chunk(file):
    length = file.read(4)  
    t = file.read(4)
    data = file.read(int.from_bytes(length, byteorder='big'))
    crc = file.read(4)
    
    return Chunk(length, t, data, crc)

def crypto_image(png,key_len):
    png.process_IDAT_image()
    png.write_encrypted_image_ECB(key_len)
    png.show_image()

def decrypto_image(png):
    img = plt.imread(img_name)
    plt.figure(num=1)
    plt.imshow(img)
    png.read_encrypted_image_ECB()


png = PNG()
img_name = "new_file.png"
mode = 2
key_length = 1024

with open(img_name, 'rb') as f:
    b = f.read(8)

    assert b == png.first_eight_bytes, "This ain't PNG"
    print('This is a PNG file!')


    while True:
        c = extract_data_from_chunk(f)
        png.chunks.append(c)
        if c.type == b'IEND':
            png.read_IEND_message(f)
            break

png.read_data_from_chunks()

if mode == 1: crypto_image(png,key_length)
elif mode == 2 : decrypto_image(png)

png.show_write_new_img()


plt.show()