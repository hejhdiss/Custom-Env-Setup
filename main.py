# @hejhdiss (Muhammed Shafin P)
#Licensed under GPLV3


from ctypes import CDLL, c_int, c_ubyte, create_string_buffer, POINTER,c_char
import os
from hashlib import blake2s
import os
import json
import hmac
import mmap
lib = CDLL("./crypto.dll")
KEY_SIZE = 32
NONCE_SIZE = 12
TAG_SIZE = 16

class Generate:
    def __init__(self,name:str,key:str)->None:
        self.path=name
        self.key=key
        self.key_=blake2s(key.encode(),key=self.key.encode()).digest()
        if not os.path.exists(name):
            raise ValueError('Not a Valid Path')
        self.fpath=os.path.abspath(name)
        self.dir=os.path.dirname(self.fpath)
        self.name_f=os.path.splitext(name)[0]
        self.ext=os.path.splitext(name)[1]
        self.gen_f=os.path.join(self.dir,self.name_f+self.ext+'.compiled')
        self.k={}
        self.filereader()
        self.filegenerator()
    def filereader(self):
        with open(self.fpath,'r+',newline='')as f:
            while True:
                line=f.readline()
                if not line:
                        break
                line=line.strip('\n')
                line=line.strip()
                a=line.find('=')
                if a==-1:
                        continue
                self.k[line[:a].strip()]=line[a+1:].strip()
    def filegenerator(self):
        self.value=json.dumps(self.k)
        self.value_=self.value.encode()
        key_buffer = (c_ubyte * KEY_SIZE).from_buffer_copy(self.key_)
        nonce = os.urandom(NONCE_SIZE)
        self.nonce=nonce
        nonce_buffer = (c_ubyte * NONCE_SIZE).from_buffer_copy(nonce)
        pt_len = len(self.value_)
        self.pt_len=pt_len
        pt_buffer = (c_ubyte * pt_len).from_buffer_copy(self.value_)
        ciphertext = create_string_buffer(pt_len)
        tag = create_string_buffer(TAG_SIZE)
        lib.chacha_encrypt.argtypes = [
        POINTER(c_ubyte), c_int, POINTER(c_ubyte), POINTER(c_ubyte),
        POINTER(c_char), POINTER(c_char)
                    ]
        lib.chacha_encrypt.restype = c_int
        cipher_len = lib.chacha_encrypt(
        pt_buffer,       # plaintxt
        pt_len,          # plaintxt  len
        key_buffer,      # key
        nonce_buffer,    # nonce
        ciphertext,      # ciphertxt
        tag              # tag 
        )
        if cipher_len == -1:
            raise ValueError("Encryption failed")
        self.cipher_len=cipher_len
        #[hash (32 bytes) | nonce (12) | tag (16) | ciphertext (cipher_len)]
        compiled_data = nonce + tag.raw + ciphertext.raw[:cipher_len]
        self.compiled_=blake2s(compiled_data).digest()
        with open(self.gen_f, 'wb') as f:
            f.write(cipher_len.to_bytes(4,'big')) # 4
            f.write(self.compiled_)      # 32
            f.write(nonce)               # 12 
            f.write(tag.raw)             # 16 
            f.write(ciphertext.raw[:cipher_len])  # ciphertxt
        with open(self.fpath,'wb') as f:
             f.truncate(4)
        os.remove(self.fpath)
class Getter:
    def __init__(self,path:str,key:str) -> None:
        self.path=path
        self.key=key
        self.env={}
        self.key_=blake2s(key.encode(),key=self.key.encode()).digest()
        if not os.path.exists(path):
             raise ValueError('Not a Valid Path')
        self.fpath=os.path.abspath(self.path)
        with open(self.fpath,'rb') as f:
            with mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as mm:
                MIN_HEADER_SIZE=64
                if len(mm) < MIN_HEADER_SIZE:
                    raise ValueError("Corrupt file")
                self.cipher_len=int.from_bytes(mm[:4],'big')
                total_needed=MIN_HEADER_SIZE+self.cipher_len
                if len(mm) < total_needed:
                    raise ValueError("Truncated ciphertext")
                self.compiled_=mm[4:36]
                self.nonce=mm[36:48]
                self.tag=mm[48:64]
                middleno=64+self.cipher_len
                self.ciphertext=mm[64: middleno]
                self.compiled=self.nonce+self.tag+self.ciphertext
                if not hmac.compare_digest(self.compiled_,blake2s(self.compiled).digest()):
                    self.env=None
                else:
                    lib.chacha_decrypt.argtypes = [
                    POINTER(c_ubyte), c_int, POINTER(c_ubyte), POINTER(c_ubyte),
                    POINTER(c_ubyte), POINTER(c_char)
                    ]
                    lib.chacha_decrypt.restype = c_int
                    key_buffer = (c_ubyte * KEY_SIZE).from_buffer_copy(self.key_)
                    nonce_buffer = (c_ubyte * NONCE_SIZE).from_buffer_copy(self.nonce)
                    ciphertext_buffer = (c_ubyte * self.cipher_len).from_buffer_copy(self.ciphertext)
                    tag_buffer = (c_ubyte * TAG_SIZE).from_buffer_copy(self.tag)
                    decrypted = create_string_buffer(self.cipher_len)
                    dec_len = lib.chacha_decrypt(
                    ciphertext_buffer,
                    self.cipher_len,
                    tag_buffer,
                    key_buffer,
                    nonce_buffer,
                    decrypted
                    )
                    if dec_len == -1:
                        self.env=None
                    else:
                        json_bytes = decrypted.raw[:dec_len]
                        self.env = json.loads(json_bytes.decode('utf-8',errors='strict'))
        
                




        
    



        


    



    



    


