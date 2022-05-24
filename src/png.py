"""
PNG file format
"""

import struct
import zlib
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image


class PNG:
    def __init__(self):
        self.text = []
        self.keyword = []
        self.chunks = []
        self.first_eight_bytes = b'\x89PNG\r\n\x1a\n'
        self.IDAT_data = b''
        self.raw_image = []
        self.IHDR_chunks = 0
        self.IDAT_chunks = 0
        self.PLTE_chunks = 0

    def __str__(self):
        s = ''.join(self.chunks)

    def read_data(self):
        for chunk in self.chunks:
            if chunk.type == b'IHDR':
                self.read_IHDR_chunk(chunk.data)
            elif chunk.type == b'IDAT':
                self.read_IDAT_chunk(chunk.data)
            elif chunk.type == b'IEND':
                self.read_IEND_chunk()
            elif chunk.type == b'PLTE':
                self.read_PLTE_chunk(chunk)
            elif chunk.type == b'tIME':
                self.read_TIME_chunk(chunk.data)
            elif chunk.type == b'gAMA':
                self.read_gAMA_chunk(chunk.data)
            elif chunk.type == b'tEXt':
                self.read_tEXt_chunk(chunk.data, chunk.length)

    def read_IHDR_chunk(self, chunk_data):
        self.width = int.from_bytes(chunk_data[0:4], 'big')
        self.height = int.from_bytes(chunk_data[4:8], 'big')
        self.depth = chunk_data[8]
        self.color_type = chunk_data[9]
        self.compression = chunk_data[10]
        self.filter = chunk_data[11]
        self.splot = chunk_data[12]
        print(f"Width: {self.width}\nHeight: {self.height}\n" f"Depth: {self.depth}\nColor type: {self.color_type}\n"
              f"Compression: {self.compression} \nFilter: {self.filter} \nSplot: {self.splot}")

        self.bytesPerPixel = {
            0: 1,  # Grayscale
            2: 3,  # Truecolor -- PLTE[optional]
            3: 1,  # Indexed  -- PLTE
            4: 2,  # Grayscale nad alpha
            6: 4  # Truecolor and alpha -- PLTE[optional]
        }[self.color_type]

    def read_IEND_chunk(self):
        print(f"IEND")

    def read_IDAT_chunk(self, data):
        self.IDAT_data += data

    def read_PLTE_chunk(self, chunk):
        self.PLTE_chunks += 1
        # assert self.PLTE_chunks == 1, "Invalid number of PLTE chunks"
        # assert self.color_type != 0 and self.color_type != 4, "PLTE chunk appear with wrong color type"
        # assert int.from_bytes(chunk.length, byteorder='big')%3 == 0, "Invalid length of PLTE chunk"
        self.palette = [x for x in chunk.data]
        # print(f"Dlugosc palety {int.from_bytes(chunk.length, byteorder='big')}")

    def show_IDAT_image(self):
        self.IDAT_data = zlib.decompress(self.IDAT_data)

        def Paeth(a, b, c):
            p = a + b - c
            pa = abs(p - a)
            pb = abs(p - b)
            pc = abs(p - c)
            if pa <= pb and pa <= pc:
                Pr = a
            elif pb <= pc:
                Pr = b
            else:
                Pr = c
            return Pr

        Recon = []

        stride = self.width * self.bytesPerPixel

        def Recon_a(r, c):
            return Recon[r * stride + c - self.bytesPerPixel] if c >= self.bytesPerPixel else 0

        def Recon_b(r, c):
            return Recon[(r - 1) * stride + c] if r > 0 else 0

        def Recon_c(r, c):
            return Recon[(r - 1) * stride + c - self.bytesPerPixel] if r > 0 and c >= self.bytesPerPixel else 0

        i = 0
        for r in range(self.height):  # for each scanline
            filter_type = self.IDAT_data[i]  # first byte of scanline is filter type
            i += 1
            for c in range(stride):  # for each byte in scanline
                Filt_x = self.IDAT_data[i]
                i += 1
                if filter_type == 0:  # None
                    Recon_x = Filt_x
                elif filter_type == 1:  # Sub
                    Recon_x = Filt_x + Recon_a(r, c)
                elif filter_type == 2:  # Up
                    Recon_x = Filt_x + Recon_b(r, c)
                elif filter_type == 3:  # Average
                    Recon_x = Filt_x + (Recon_a(r, c) + Recon_b(r, c)) // 2
                elif filter_type == 4:  # Paeth
                    Recon_x = Filt_x + Paeth(Recon_a(r, c), Recon_b(r, c), Recon_c(r, c))
                else:
                    raise Exception('unknown filter type: ' + str(filter_type))
                Recon.append(Recon_x & 0xff)  # truncation to byte

        if self.PLTE_chunks == 1:  # insert palette colors
            if self.color_type == 2 or self.color_type == 3:  # Indexed without alpha
                i = 0;
                for x in Recon:
                    self.raw_image.append(self.palette[x * 3:x * 3 + 3])
                self.raw_image = np.array(self.raw_image).reshape(self.height, self.width, 3)
            else:  # Indexed with alpha
                for x in Recon:
                    if i == 0:
                        self.raw_image.append(self.palette[x * 4:x * 4 + 3])
                    else:
                        self.raw_image.append(x)
                    i = (i + 1) % 2
                self.raw_image = np.array(self.raw_image).reshape(self.height, self.width, 4)
        else:
            self.raw_image = np.array(Recon).reshape(self.height, self.width, self.bytesPerPixel)
        plt.figure(num=0)
        if self.bytesPerPixel == 2:
            print("")
        else:
            plt.imshow(self.raw_image, cmap='gray')



    def read_TIME_chunk(self, chunk_data):
        data_values = struct.unpack('>hbbbbb', chunk_data)
        self.year = data_values[0]
        self.month = data_values[1]
        self.day = data_values[2]
        self.hour = data_values[3]
        self.minute = data_values[4]
        self.second = data_values[5]
        print(f"Last modification: {self.day} {self.month} {self.year} {self.hour}:{self.minute}:{self.second}")

    def read_gAMA_chunk(self, chunk_data):
        self.gamma = int.from_bytes(chunk_data, 'big') / 1000
        print(f"gamma = {self.gamma}")

    def read_tEXt_chunk(self, chunk_data, chunk_length):
        global str1, str2
        i = 0
        length = int.from_bytes(chunk_length, "big")

        while chunk_data[i] != 0:
            self.keyword.append(chunk_data[i])
            i = i + 1
        while i < length:
            self.text.append(chunk_data[i])
            i = i + 1
        str1 = ''
        str2 = ''
        for i in self.keyword:
            str1 += chr(i)
        for i in self.text:
            str2 += chr(i)
        print(f"tEXt chunk keyword: {str1}\ntext: {str2}\n")

    def show_spectrum(self):
        if self.color_type == 0:
            raw_image_gray = self.raw_image
        else:
            raw_image_gray = np.dot(self.raw_image[..., :3], [0.2989, 0.5870, 0.1140])
            plt.figure(num=1)
            plt.imshow(raw_image_gray, cmap='gray')
            spectrum = np.fft.fftshift(np.fft.fft2(raw_image_gray))
            plt.figure(num=2)
            plt.imshow(np.log(abs(spectrum)), cmap='gray')
            plt.figure(num=3)
            plt.imshow(np.angle(spectrum), cmap='gray')

    def delete_ancillary_chunks(self):
        for chunk in self.chunks[:]:
            if chr(chunk.type[0]).islower():
                self.chunks.remove(chunk)

    def show_write_new_img(self):
        with open('new_file.png', 'wb') as file:
            file.write(self.first_eight_bytes)
            for chunk in self.chunks:
                file.write(chunk.length)
                file.write(chunk.type)
                file.write(chunk.data)
                file.write(chunk.crc)
        img = plt.imread('new_file.png')
        plt.imshow(img)
