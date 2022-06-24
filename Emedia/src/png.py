"""
class represents a PNG file format
"""
from src.chunk import Chunk
from src.rsa import RSA
import zlib
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import math

class PNG:
    def __init__(self):
        self.chunks = []
        self.first_eight_bytes = b'\x89PNG\r\n\x1a\n'
        self.IDAT_data = b''
        self.raw_image = []
        self.IHDR_chunks = 0 
        self.IDAT_chunks = 0
        self.IDAT_data_length = 0
        self.PLTE_chunks = 0
        self.IEND_chunks = 0
        self.alpha = []
        self.secretMessage = b''
        self.secret_IDAT_message = b''

    def __str__(self):
        s = ''.join(self.chunks)
       
    def read_data_from_chunks(self):
        for chunk in self.chunks:
            if chunk.type == b'IHDR':
                self.read_IHDR_chunk(chunk.data)
            elif chunk.type == b'IDAT':
                self.read_IDAT_chunk(chunk)
            elif chunk.type == b'IEND':
                self.read_IEND_chunk(chunk.length)
            elif chunk.type == b'PLTE':
                self.read_PLTE_chunk(chunk)
            elif chunk.type == b'tEXt':
                self.read_tEXt_chunk(chunk)
            elif chunk.type == b'gAMA':
                assert self.IDAT_chunks == 0 and self.PLTE_chunks == 0, "gAMA chunk cannot appear after either PLTE or IDAT chunk"
                self.read_gAMA_chunk(chunk)
        #self.process_IDAT_image()
        assert self.IDAT_chunks >= 1, "IDAT chunk not found"
        assert self.IEND_chunks == 1, "IEND chunk not found"


    def read_gAMA_chunk(self, chunk):
        print(f'- {chunk.type.decode("utf-8")} chunk')
        print(f'  + Image gamma: {int.from_bytes(chunk.data, "big")}')

                    

    def read_tEXt_chunk(self, chunk):
        print(f'- {chunk.type.decode("utf-8")} chunk')
        data = chunk.data.split(b'\x00')
        print(f'  + {data[0].decode("utf-8")}: {data[1].decode("utf-8")}')
                    
    def read_IHDR_chunk(self,chunk_data):
        self.IHDR_chunks += 1
        assert self.IHDR_chunks == 1, "Too many IHDR chunks"
        
        self.width      = int.from_bytes(chunk_data[0:4], 'big')
        self.height     = int.from_bytes(chunk_data[4:8], 'big')
        self.depth      = chunk_data[8]
        self.color_type = chunk_data[9]
        self.compression= chunk_data[10]
        self.filter     = chunk_data[11]
        self.cos        = chunk_data[12]
        print(f"Width: {self.width}\nHeight: {self.height}\n"
              f"Depth: {self.depth}\ncolor type: {self.color_type}\n"
              f"compression: {self.compression} \nFilter: {self.filter} \n"
              f"Interlace method {self.cos}\n")
        

        self.bytesPerPixel = {
            0: 1, #Grayscale
            2: 3, #Truecolor -- PLTE[optional]
            3: 1, #Indexed  -- PLTE
            4: 2, #Grayscale nad alpha
            6: 4  #Truecolor and alpha -- PLTE[optional]
            }[self.color_type]
        
    def read_IEND_chunk(self, length):
        self.IEND_chunks += 1
        assert int.from_bytes(length, byteorder='big') == 0, f"Invalid length of IEND chunk {length}"
        self.read_secret_message()
        
    def read_IDAT_chunk(self, chunk):
        self.IDAT_chunks += 1
        assert self.IHDR_chunks == 1, "IDAT chunk cannot appear before IHDR chunk"
        data_length = int.from_bytes(chunk.length, byteorder='big')
        if data_length == 0:
            self.secret_IDAT_message += chunk.crc
        else: 
            self.IDAT_data += chunk.data
            self.IDAT_data_length += data_length
        
    def read_PLTE_chunk(self,chunk):
        self.PLTE_chunks += 1
        assert self.PLTE_chunks == 1, "Invalid number of PLTE chunks"
        assert self.IDAT_chunks == 0, "IDAT chunk cannot appear before PLTE chunk"
        assert self.color_type not in [0, 4], "PLTE chunk appear with wrong color type"
        assert int.from_bytes(chunk.length, byteorder='big')%3 == 0, "Invalid length of PLTE chunk"
        number_of_indexes = math.floor(int.from_bytes(chunk.length, byteorder='big')/3)
        
        self.palette = [x for x in chunk.data]
        
        #=== Shows palette index values ===
        print(f"===== PALETTE({number_of_indexes}) =======\nIndex          R,G,B\n")
        for x in range(number_of_indexes):
            tmp_str = "".ljust(12 - math.floor(math.log10(max(x,1))))
            print(f"  {x}{tmp_str}{self.palette[x*3]},{self.palette[x*3+1]},{self.palette[x*3+2]}")
        #self.pallete = np.array(chunk.data).reshape(chunk.length/3,3)  
        
    def process_IDAT_image(self,mode = 0):
        if mode != "ignore_decompression": self.IDAT_data = zlib.decompress(self.IDAT_data) 
        print()
        
        def PaethPredictor(a, b, c):
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
        def byte_to_int(byte,position):
            if self.depth == 16:
                return byte           
            byte = (byte >> 8 - position - self.depth) # range (0-6)
            mask = {
                1: 0x01,
                2: 0x03,
                4: 0x0F,
                8: 0xFF
                }[self.depth]
            byte = byte & mask
            return byte
        
        def get_pixels_from_1D_array(array):
            pos = 0  
            for x in range(self.height * self.width * self.bytesPerPixel):
                pos = (pos + self.depth) % 8
                if self.depth == 16:
                    byte = (array[x*2] + 1) * (array [x*2 + 1] + 1) - 1
                else:
                    byte = array[x * self.depth // 8]
                if self.color_type == 3:
                    for j in range(3):         
                        self.raw_image.append(self.palette[byte_to_int(byte,pos) * 3 + j]) 
                else:
                    self.raw_image.append(byte_to_int(byte, pos))
                if len(self.alpha) > 0: self.raw_image.append(self.alpha[byte_to_int(byte,pos)]) 
            if self.PLTE_chunks == 1: self.bytesPerPixel = 3
            if len(self.alpha) > 0: self.bytesPerPixel += 1
            self.raw_image = np.array(self.raw_image).reshape(self.height,self.width,self.bytesPerPixel)
            return 1
        
                
        def Recon_a(r, c):
            return Recon[r * stride + c - self.bytesPerPixel] if c >= self.bytesPerPixel else 0

        def Recon_b(r, c):
            return Recon[(r-1) * stride + c] if r > 0 else 0

        def Recon_c(r, c):
            return Recon[(r-1) * stride + c - self.bytesPerPixel] if r > 0 and c >= self.bytesPerPixel else 0
        
        Recon = []
        stride = self.width * self.bytesPerPixel * self.depth // 8
        
        
        

        i = 0
        for r in range(self.height): # for each scanline
            filter_type = self.IDAT_data[i]#byte_to_int(i,pos) # first byte of scanline is filter type
            i += 1
            for c in range(stride): # for each byte in scanline
                Filt_x = self.IDAT_data[i]#byte_to_int(i,pos)
                i += 1
                if filter_type == 0: # None
                    Recon_x = Filt_x
                elif filter_type == 1: # Sub
                    Recon_x = Filt_x + Recon_a(r, c)
                elif filter_type == 2: # Up
                    Recon_x = Filt_x + Recon_b(r, c)
                elif filter_type == 3: # Average
                    Recon_x = Filt_x + (Recon_a(r, c) + Recon_b(r, c)) // 2
                elif filter_type == 4: # Paeth
                    Recon_x = Filt_x + PaethPredictor(Recon_a(r, c), Recon_b(r, c), Recon_c(r, c))
                else:
                    Recon_x = Filt_x
                    raise Exception(f'unknown filter type: {filter_type} in {i} |stride - {stride}')
                Recon.append(Recon_x & 0xff) # truncation to byte
        #print(f"Recon - {Recon}")
        get_pixels_from_1D_array(Recon)

        
        
                
        
                
    def show_image(self):
        plt.figure(num=0)
        if self.bytesPerPixel == 1:   #Grayscale
            plt.imshow(self.raw_image,cmap = 'gray')
        elif self.bytesPerPixel == 2: #Grayscale with alpha
            grayscale = self.raw_image[:,:,0]
            alpha = self.raw_image[:,:,1]
            tmp_img = np.dstack((grayscale,grayscale,grayscale,alpha))
            plt.imshow(tmp_img)
        else:
            plt.imshow(self.raw_image)                
        
        
    def show_spectrum(self):
        color_range = 2 ** self.depth - 1
        if self.color_type == 0: 
            raw_image_gray = self.raw_image
        elif self.color_type == 4:
            raw_image_gray = self.raw_image[:,:,0]
        else: 
            raw_image_gray = np.dot(self.raw_image[...,:3],[0.2989, 0.5870, 0.1140])
            if self.bytesPerPixel == 4: raw_image_gray = raw_image_gray * self.raw_image[:, :, 3]//255 + 255 - self.raw_image[:, :, 3]
            
        spectrum = np.fft.fftshift(np.fft.fft2(raw_image_gray))
        plt.figure(num=2)
        plt.imshow(np.log10(np.abs(spectrum)),cmap='gray')
        plt.figure(num=3)
        plt.imshow(np.angle(spectrum),cmap='gray')
    
    def get_decompress_IDAT(self):
        return zlib.compress(self.IDAT_data)
        
    def read_IEND_message(self, file):
        
        while (byte := file.read(1)) != '':
            if byte == b'':
                print("EOF")
                break
            self.secretMessage += byte
            
    def read_secret_message(self):
        i = 0
        message = b''
        while True:
            if i < len(self.secret_IDAT_message):
                message += self.secret_IDAT_message[i:i+4]
                message += self.secretMessage[i:min(i+4,len(self.secretMessage))]
            else:
                message += self.secretMessage[i:min(i+4,len(self.secretMessage))]
                break
            i += 4
        return message
        
    '''
    4 IDAT 4 Koniec pliku
    '''
    def write_secret_message(self, message, mode=0):
        IEND_chunk = self.chunks.pop()
        if mode == 0: 
            self.secretMessage = b''
            for chunk in self.chunks[:]:
                if chunk.type == b'IDAT' and int.from_bytes(chunk.length, "big") == 0:
                    self.chunks.remove(chunk)
        i = 0
        while i < len(message):
            next_val = min(len(message),i + 4)
            if i + 4 == next_val and i % 8 == 0:
                new_empty_chunk = Chunk(b'\x00\x00\x00\x00',b'IDAT',b'',message[i:i+4])
                self.chunks.append(new_empty_chunk)
            else:
                self.secretMessage += message[i:next_val]
            i = next_val
        self.chunks.append(IEND_chunk)
        
    def one_IDAT_before_IEND(self,new_IDAT_chunk,secret_data):
        IEND_chunk = self.chunks.pop() #Zapisujemy IEND na pozniej
        self.chunks.append(new_IDAT_chunk)
        self.chunks.append(IEND_chunk)
        self.write_secret_message(secret_data)
        
 
    def write_encrypted_image_ECB(self,RSA_len):
        def array_int_to_array_byte(data):
            i = 0
            byte_data = b''
            while i < len(data):
                int = data[i].item()
                byte_data += int.to_bytes(1, byteorder = 'big')
                i += 1
            return byte_data
                
        self.rsa = RSA(RSA_len)
        self.rsa.generate_keys() 
        data_to_cipher = self.raw_image.ravel() 
        data_to_cipher = array_int_to_array_byte(data_to_cipher)
        ciphered_data = self.rsa.crypto_ECB(data_to_cipher) 
        new_IDAT_chunk, additional_image_data = self.split_ciphered_data(ciphered_data) 
        new_IDAT_chunk = self.insert_filter_types(new_IDAT_chunk, self.width * self.bytesPerPixel)
        new_IDAT_chunk = zlib.compress(new_IDAT_chunk) 
        additional_image_data = zlib.compress(additional_image_data)
        self.one_IDAT_before_IEND(self.create_one_IDAT(new_IDAT_chunk), self.rsa.get_key_data()+additional_image_data)

        
    def read_encrypted_image_ECB(self):
        secret_message = self.read_secret_message() 
        d_len = int.from_bytes(secret_message[0:4], byteorder = 'big')
        n_len = int.from_bytes(secret_message[4:8], byteorder = 'big')
        last_block_len = int.from_bytes(secret_message[8:12], byteorder = 'big')
        d_block_end = 12 + d_len
        n_block_end = d_block_end + n_len
        d = int.from_bytes(secret_message[12:d_block_end], byteorder = 'big')
        n = int.from_bytes(secret_message[d_block_end:n_block_end], byteorder = 'big')
        additional_IDAT_data = secret_message[n_block_end:] 
        additional_IDAT_data = zlib.decompress(additional_IDAT_data) 
      
        self.rsa = RSA(n_len * 8)
        self.rsa.load_private_key(d,n)
        self.rsa.set_last_block_length(last_block_len)
     
        data_to_decrypt = self.get_data_without_filter_byte()
        data_to_decrypt = self.merge_bytes_data(data_to_decrypt,additional_IDAT_data)
        self.IDAT_data = self.rsa.decrypto_ECB(data_to_decrypt)
        self.IDAT_data = self.insert_filter_types(self.IDAT_data, self.width * self.bytesPerPixel)
        self.one_IDAT_before_IEND(self.create_one_IDAT(zlib.compress(self.IDAT_data)), b'')
        self.process_IDAT_image("ignore_decompression")
        
    def get_data_without_filter_byte(self):
        row_len = self.width * self.bytesPerPixel
        self.IDAT_data = zlib.decompress(self.IDAT_data) 
        data_without_filter = b''
        for i in range(self.height):
            start = i * row_len + (i + 1) 
            data_without_filter +=self.IDAT_data[start:start + row_len]
        return data_without_filter
    
    def split_ciphered_data(self,ciphered_data):
        ciphered_data_len = len(ciphered_data)
        IDAT_data = b''
        secret_data = b''
        block_start = 0
        while True:            
            block_end = block_start + self.rsa.block_length
            
            if block_end + 1 == ciphered_data_len: 
                block_end = block_start + self.rsa.last_block_length
                IDAT_data += ciphered_data[block_start:block_end]
                secret_data += ciphered_data[block_end:]
                break            
            IDAT_data += ciphered_data[block_start:block_end] #
            block_start = block_end + 1                         
            secret_data += ciphered_data[block_end].to_bytes(1, byteorder = 'big')                  
        return IDAT_data,secret_data
    

    def merge_bytes_data(self,IDAT_data,secret_data):
        block_no = 0
        block_start = 0
        block_end = 0
        merged_data = b''
        while block_start < len(IDAT_data):
            block_end = block_start + self.rsa.block_length
            if block_end >= len(IDAT_data):
                merged_data += IDAT_data[block_start:]
                merged_data += secret_data[block_no:]
                break
            merged_data += IDAT_data[block_start:block_end]
            merged_data += secret_data[block_no].to_bytes(1, byteorder = 'big')
            block_start = block_end
            block_no += 1
        return merged_data

        
    def insert_filter_types(self,content,row_length):
        return_data = b''
        zero = 0
        for i in range(self.height):
            return_data += zero.to_bytes(1, byteorder = 'big')
            return_data += content[i*row_length:(i+1)*row_length]
        return return_data
        
    def create_one_IDAT(self,content):
        self.delete_chunks([b'IHDR', b'PLTE', b'IEND',b'tRNS'])    
        return Chunk(len(content).to_bytes(4, 'big'),b'IDAT',content,(zlib.crc32(content) & 0xffffffff).to_bytes(4,byteorder = 'big'))
            

    def delete_ancillary_chunks(self):
        '''
        Metoda usuwająca tak zwane "ancillary chunks" z obrazu .png
        '''
        for chunk in self.chunks[:]:
            if chr(chunk.type[0]).islower():
                self.chunks.remove(chunk)
                
    def delete_chunks(self,chunk_type_list = [b'IHDR', b'PLTE', b'IDAT', b'IEND',b'tRNS']):
        for chunk in self.chunks[:]:
            if any(x == chunk.type for x in chunk_type_list) == False:
                self.chunks.remove(chunk)
                
    def show_write_new_img(self):
        '''
        Metoda zapisuje jako "new_file.png" i wyświetla
        obraz bez ancillary chunks
        '''
        with open('new_file.png', 'wb') as file:
            file.write(self.first_eight_bytes)
            for chunk in self.chunks:
                file.write(chunk.length)
                file.write(chunk.type)
                file.write(chunk.data)
                file.write(chunk.crc)
            file.write(self.secretMessage)
        img = plt.imread('new_file.png')
        plt.figure(num=4)
        plt.imshow(img)