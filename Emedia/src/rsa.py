import sympy
import random
import time
import math


class RSA:
    def __init__(self, length):
        print("Checking key length")
        self.byte_length = length // 8
        self.block_length = self.byte_length - 1
        assert length / 8 == self.byte_length, "RSA key must be mod 8"

        self.display_info = False
        self.last_block_length = 1

        self.length = length
        self.publicKey = 0
        self.publicKey = 0

    def __str__(self):
        return f"byte_length - {self.byte_length} \npublicKey - {self.publicKey != 0} \nprivateKey - {self.private != 0}"

    def generate_keys(self):
        print(f"Key length valid \nGenerating {self.length}bit key...")
        self.publicKey, self.privateKey = self.createKeys()

    def load_private_key(self, d, n):
        self.privateKey = (d, n)

    def set_last_block_length(self, new_value):
        self.last_block_length = new_value

    def show_info(self, info):
        if self.display_info == False:
            return
        print(info)
        time.sleep(0.1)

    def crypto(self, block):
        return pow(block, self.publicKey[0], self.publicKey[1])

    def decrypto(self, block):
        return pow(block, self.privateKey[0], self.privateKey[1])

    def createKeys(self):

        def gcd(a, b):
            while b != 0:
                a, b = b, a % b
            return a

        def isCoprime(num1, num2):
            return gcd(num1, num2) == 1

        def inverse(x, m):
            a, b, u = 0, m, 1
            while x > 0:
                q = b // x
                x, a, b, u = b % x, u, x, a - q * u
            if b == 1: return a % m
            print("error must be coprime")

        def isPrime(n):
            if n % 2 == 0:
                return False
            s = n - 1
            t = 0
            while s % 2 == 0:
                s = s // 2
                t += 1
            k = 0
            while k < 5:
                a = random.randrange(2, n - 1)
                v = pow(a, s, n)
                if v != 1:
                    i = 0
                    while v != (n - 1):
                        if i == t - 1:
                            return False
                        else:
                            i = i + 1
                            v = (v ** 2) % n
                k += 2
            return True

        def return_prime(type):
            if type == "lib":
                return sympy.randprime(2 ** (self.length // 2 - 1), 2 ** (self.length // 2) - 1)

            while True:
                potential_prime = random.randrange(2 ** (self.length // 2 - 1) + 1, 2 ** (self.length // 2) - 1)
                if isPrime(potential_prime):
                    return potential_prime

        p = return_prime("custom")
        q = return_prime("custom")

        n = p * q
        o = (p - 1) * (q - 1)
        e = 0

        self.show_info(f"p - {p} \nq - {q} \nn - {n} \no - {o} \ne - {e}")

        self.show_info("generating e \nChecking coprime...")
        while True:
            e = random.randrange(2, min(o - 1, 2 ** 16))
            if isCoprime(e, o):
                break

        d = inverse(e, o)

        publicKey = (e, n)
        privateKey = (d, n)

        return publicKey, privateKey

    def crypto_ECB(self, data):
        data_length = len(data)
        ciphered_data = b''
        self.show_info(f"Prediction: {int(math.ceil(data_length / self.block_length))}")
        block_start = 0
        while block_start < data_length:
            block_end = min(block_start + self.block_length, data_length)
            self.show_info(f"Cipher block start {block_start}, block end {block_end}")
            cipher_block = int.from_bytes(data[block_start:block_end], byteorder="big")
            ciphered_block = self.crypto(cipher_block)
            self.show_info(f"{cipher_block} -> {ciphered_block}")
            ciphered_block_byte = ciphered_block.to_bytes(self.byte_length, byteorder='big')
            if block_end == data_length:
                self.last_block_length = block_end - block_start
            self.show_info(
                f"{data[block_start:block_end]} -> {cipher_block} -> {ciphered_block} -> {ciphered_block_byte}")
            ciphered_data += ciphered_block_byte
            block_start += self.block_length
        return ciphered_data

    def decrypto_ECB(self, data):
        data_length = len(data)
        assert data_length % self.byte_length == 0, "Invalid length of data to decrypt"
        decrypted_data = b''
        block_start = 0
        while block_start < data_length:
            block_end = block_start + self.byte_length

            decrypto_block = int.from_bytes(data[block_start:block_end], byteorder='big')
            decrypted_block = self.decrypto(decrypto_block)
            if block_end == data_length:
                decrypted_block_byte = decrypted_block.to_bytes(self.byte_length - 1, byteorder='big')
                decrypted_block_byte = decrypted_block_byte[0:self.last_block_length]
            else:
                self.show_info(f"Convert {decrypto_block} ->{decrypted_block}")
                decrypted_block_byte = decrypted_block.to_bytes(self.byte_length - 1, byteorder='big')

            self.show_info(
                f"{data[block_start:block_end]} -> {decrypto_block} -> {decrypted_block} -> {decrypted_block_byte}")
            decrypted_data += decrypted_block_byte
            block_start += self.byte_length
        return decrypted_data

    def get_key_data(self):
        d_len = (self.privateKey[0].bit_length() + 7) // 8
        last_block_len = self.last_block_length.to_bytes(4, byteorder='big')
        print(f"Zapisuje... \nd - {self.privateKey[0]} \nn - {self.privateKey[1]} \nlast_block - {last_block_len}")
        d = self.privateKey[0].to_bytes(d_len, byteorder='big')
        n = self.privateKey[1].to_bytes(self.byte_length, byteorder='big')
        d_len = d_len.to_bytes(4, byteorder='big')
        n_len = self.byte_length.to_bytes(4, byteorder='big')

        return d_len + n_len + last_block_len + d + n
