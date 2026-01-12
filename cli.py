# @hejhdiss (Muhammed Shafin P)
#Licensed under GPLV3


from ctypes import CDLL, c_int, c_ubyte, create_string_buffer, POINTER,c_char
import os
from hashlib import blake2s,pbkdf2_hmac
import argparse
import os
import json
import logging
import datetime
import sys
lib = CDLL("./crypto.dll")
KEY_SIZE = 32
NONCE_SIZE = 12
TAG_SIZE = 16

class Generate:
    def __init__(self,name:str,key:str,arg:bool)->None:
        self.path=name
        self.key=key
        self.arg=arg
        nonce = os.urandom(NONCE_SIZE)
        self.nonce=nonce
        self.key_=self.key_ = pbkdf2_hmac(
    'sha256',
    key.encode('utf-8'),
    self.nonce,     
    300_000,         
    dklen=32
)
        if not os.path.exists(name):
            raise ValueError
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
        nonce_buffer = (c_ubyte * NONCE_SIZE).from_buffer_copy(self.nonce)
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
            raise TypeError
        self.cipher_len=cipher_len
        #[hash (32 bytes) | nonce (12) | tag (16) | ciphertext (cipher_len)]
        compiled_data = self.nonce + tag.raw + ciphertext.raw[:cipher_len]
        self.compiled_=blake2s(compiled_data).digest()
        with open(self.gen_f, 'wb') as f:
            f.write(cipher_len.to_bytes(4,'big')) # 4
            f.write(self.compiled_)      # 32
            f.write(self.nonce)               # 12 
            f.write(tag.raw)             # 16 
            f.write(ciphertext.raw[:cipher_len])  # ciphertxt
        if not self.arg:
            with open(self.fpath,'wb') as f:
                f.truncate(4)
            os.remove(self.fpath)
if __name__=='__main__':
    parser=argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,prog='Custom env setup',description='Allows encrypted setup of the env for Python scripts.',epilog=(
          'Copyright @hejhdiss (Muhammed Shafin P)\n'
          'Based on openssl\n'
          'Licensed under GPLV3.'
     ))
    parser.add_argument('-k','--key',help='Key required for encryption.',metavar='MY_SECRET_KEY',required=True,action='store')
    parser.add_argument('-f','--file',help='File path of current env file.',metavar='/path/to/file',required=True,action='store')
    parser.add_argument('-n',help='Enables flag to keep the env file.',required=False,action='store_true')
    args=parser.parse_args()
    logger=logging.getLogger(__name__)
    handler=logging.StreamHandler()
    ab=datetime.datetime.now().isoformat(sep=' ')
    ab="%(asctime)s - %(levelname)s - %(message)s"
    formatter=logging.Formatter(ab)
    handler.setFormatter(formatter)
    logger.setLevel(logging.ERROR)
    logger.addHandler(handler)
    try:
        a=Generate(args.file,args.key,args.n)
    except ValueError:
        logger.error('Given path is not a valid path.')
        sys.exit(1)
    except TypeError:
        logger.error('Encryption Failed.')
    else:
        logger.setLevel(logging.INFO) 
        logger.info(f'Generated at : {a.gen_f}. ')
        
         
         
         


