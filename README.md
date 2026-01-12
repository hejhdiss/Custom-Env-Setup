# Encrypted Environment Manager

A custom environment variable encryption tool for Python developers that provides secure storage of sensitive configuration data using ChaCha20-Poly1305 encryption and BLAKE2s hashing.

## Overview

This is my original design and implementation - a custom solution I created from scratch after seeing developers online struggling with `.env` file security. I noticed that `.env` files are inherently insecure when stored in repositories or shared across teams, so I designed this encryption-based approach to solve that problem.

The tool encrypts `.env` files and other configuration files, making them safe to store in version control or share across teams without exposing sensitive credentials.

## Why This Tool?

I came across discussions online about the security risks of `.env` files - they're plain text and easily exposed if accidentally committed to version control or shared insecurely. I designed and built this solution from the ground up to address that problem. The combination of **ChaCha20-Poly1305** for encryption and **BLAKE2s** for integrity verification ensures:

- **Speed**: ChaCha20-Poly1305 is optimized for performance on any device, including mobile and embedded systems
- **Security**: AEAD (Authenticated Encryption with Associated Data) protects against tampering
- **Portability**: BLAKE2s provides fast, cryptographic hashing that works efficiently across platforms
- **Simplicity**: Easy-to-use CLI for developers who just want things to work

## Features

- 🔒 **Strong Encryption**: ChaCha20-Poly1305 AEAD cipher
- ✅ **Integrity Verification**: BLAKE2s hashing prevents tampering
- 🚀 **Fast Performance**: Optimized for speed on any device
- 🔑 **Key-based Security**: Password-derived encryption keys
- 📦 **Compiled Output**: Creates `.compiled` files for secure distribution
- 🗑️ **Auto-cleanup**: Optionally removes original files after encryption

## Requirements

- Python 3.x
- `crypto.dll` (compiled for Win64 - included)

**Note**: The `crypto.dll` is pre-compiled for Windows 64-bit systems using **OpenSSL 3.6** with the library statically linked. This means:
- ✅ **If you use the provided `crypto.dll`**: No additional OpenSSL installation needed - everything is included in the compiled DLL
- ⚠️ **If you manually compile for your platform**: You'll need OpenSSL 3.6+ installed on your system and should remove/replace the provided `crypto.dll`

## Installation

1. Clone or download this repository
2. Ensure `crypto.dll` is in the same directory as the Python scripts
3. Install Python 3.x if not already installed

## Usage

### Encrypting Environment Files

Use `cli.py` to encrypt your environment files:

```bash
python cli.py -k YOUR_SECRET_KEY -f path/to/your.env
```

**Options**:
- `-k, --key`: Encryption key (required)
- `-f, --file`: Path to the environment file (required)
- `-n`: Keep the original file after encryption (optional)

**Example**:
```bash
# Encrypt and remove original
python cli.py -k mySecretPassword123 -f .env

# Encrypt but keep original
python cli.py -k mySecretPassword123 -f .env -n
```

### Loading Encrypted Variables

Use the `Getter` class from `main.py` to load encrypted environment variables in your Python scripts:

```python
from main import Getter

# Load encrypted environment variables
env_loader = Getter('path/to/file.env.compiled', 'YOUR_SECRET_KEY')

# Access variables
if env_loader.env:
    db_password = env_loader.env.get('DB_PASSWORD')
    api_key = env_loader.env.get('API_KEY')
else:
    print("Failed to decrypt or file was tampered with")
```

## File Format

### Input (.env file)
```
DATABASE_URL=postgresql://localhost/mydb
API_KEY=abc123xyz
SECRET_TOKEN=super_secret_value
```

### Output (.env.compiled)
Binary file structure:
```
[4 bytes: cipher_len] [32 bytes: hash] [12 bytes: nonce] [16 bytes: tag] [variable: ciphertext]
```

## How It Works

1. **Encryption Process**:
   - Reads key-value pairs from environment file
   - Converts to JSON format
   - Derives 32-byte key from password using BLAKE2s
   - Generates random 12-byte nonce
   - Encrypts with ChaCha20-Poly1305
   - Creates integrity hash of encrypted data
   - Writes compiled binary file

2. **Decryption Process**:
   - Reads compiled file using memory mapping
   - Verifies integrity hash
   - Decrypts using ChaCha20-Poly1305
   - Returns dictionary of environment variables

## Security Notes

- Never commit your encryption keys to version control
- Store keys in secure key management systems (e.g., HashiCorp Vault, AWS Secrets Manager)
- The `.compiled` files are safe to commit but useless without the encryption key
- BLAKE2s verification ensures files haven't been tampered with

## Compiling crypto.dll for Other Platforms

The provided `crypto.dll` for Windows includes OpenSSL 3.6 statically linked, so no external dependencies are needed.

**If you need to compile for other platforms, you have two options:**

### Option 1: Dynamic Linking (Requires OpenSSL on Target System)

This creates a smaller library file but requires users to have OpenSSL installed.

**Linux:**
```bash
# Install OpenSSL development libraries first
sudo apt-get install libssl-dev  # Debian/Ubuntu
# OR
sudo yum install openssl-devel   # RHEL/CentOS

# Compile with dynamic linking
gcc -shared -fPIC -o crypto.so encrypt.c -lssl -lcrypto
```

**macOS:**
```bash
# Install OpenSSL (if not already installed)
brew install openssl

# Compile with dynamic linking
gcc -shared -fPIC -o crypto.dylib encrypt.c -lssl -lcrypto
```

### Option 2: Static Linking (Self-Contained, No Dependencies)

This includes OpenSSL libraries directly in the binary (like the provided Windows DLL). Users won't need OpenSSL installed.

**Linux:**
```bash
# Install OpenSSL development libraries
sudo apt-get install libssl-dev

# Compile with static linking (includes OpenSSL in binary)
gcc -shared -fPIC -o crypto.so encrypt.c \
    /usr/lib/x86_64-linux-gnu/libssl.a \
    /usr/lib/x86_64-linux-gnu/libcrypto.a \
    -lpthread -ldl
```

**macOS:**
```bash
# Install OpenSSL
brew install openssl

# Compile with static linking
gcc -shared -fPIC -o crypto.dylib encrypt.c \
    /usr/local/opt/openssl/lib/libssl.a \
    /usr/local/opt/openssl/lib/libcrypto.a \
    -I/usr/local/opt/openssl/include
```

### Custom OpenSSL Installation Path

If you installed OpenSSL in a custom location, you can specify paths to header files and libraries:

```bash
# Linux/macOS - Custom paths
gcc -shared -fPIC -o crypto.so encrypt.c \
    -I/custom/path/to/openssl/include \
    -L/custom/path/to/openssl/lib \
    -lssl -lcrypto

# Static linking with custom paths
gcc -shared -fPIC -o crypto.so encrypt.c \
    -I/custom/path/to/openssl/include \
    /custom/path/to/openssl/lib/libssl.a \
    /custom/path/to/openssl/lib/libcrypto.a \
    -lpthread -ldl
```

### Compiler Flags Explained

- `-shared`: Create a shared library
- `-fPIC`: Position Independent Code (required for shared libraries)
- `-I<path>`: Include header files from specified path
- `-L<path>`: Look for libraries in specified path
- `-l<name>`: Link against library (e.g., `-lssl` links to libssl)
- `.a` files: Static libraries (included in your binary)
- `-lpthread -ldl`: Additional dependencies for static linking on Linux

### Static vs Dynamic Linking Trade-offs

**Static Linking** (like the provided Windows DLL):
- ✅ Self-contained - no external dependencies needed
- ✅ Easier distribution - works on any system
- ✅ No version conflicts
- ❌ Larger file size
- ❌ Security updates require recompilation

**Dynamic Linking**:
- ✅ Smaller file size
- ✅ Automatic security updates through system OpenSSL
- ✅ Shared memory with other programs using OpenSSL
- ❌ Requires OpenSSL installed on target system
- ❌ Potential version compatibility issues

**After compiling, update the library loading in Python:**
```python
# For Linux
lib = CDLL("./crypto.so")

# For macOS
lib = CDLL("./crypto.dylib")
```

**Important**: 
- When manually compiling, ensure you have OpenSSL 3.6+ installed on your system
- Remove or don't use the provided Windows `crypto.dll` if compiling for other platforms
- Choose static linking if you want a self-contained binary like the provided Windows version
- Choose dynamic linking if you want a smaller file and can ensure OpenSSL is installed on target systems

## License

Licensed under GPL v3

## Author

**@hejhdiss (Muhammed Shafin P)**

Built with OpenSSL

## Contributing

This is my original design and implementation that I created after identifying the `.env` file security problem that many developers face online. I'm sharing it because I found my own solution to this issue and thought it might help others. Feel free to fork and adapt it for your use cases. If you find bugs or have suggestions, contributions are welcome!

## Disclaimer

This tool is provided as-is for developers who need a simple encryption solution for environment variables. While it uses industry-standard encryption algorithms, please evaluate your own security requirements before use in production environments.