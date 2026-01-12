# Encrypted Environment Manager

A custom environment variable encryption tool for Python developers that provides secure storage of sensitive configuration data using ChaCha20-Poly1305 encryption and BLAKE2s hashing.

## Overview

This is my original design and implementation - a custom solution I created from scratch after seeing developers online struggling with `.env` file security. I noticed that `.env` files are inherently insecure when stored in repositories or shared across teams, so I designed this encryption-based approach to solve that problem.

**Note**: This is a proof-of-concept (PoC) implementation intended to introduce the design pattern. The main purpose is to demonstrate this approach so developers can understand, learn from, and modify it according to their specific needs. While it provides good security for development use, it intentionally uses some simplifications (like using the nonce as PBKDF2 salt) to keep the implementation clear and understandable.

The tool encrypts `.env` files and other configuration files, making them safe to store in version control or share across teams without exposing sensitive credentials.

## Why This Tool?

I came across discussions online about the security risks of `.env` files - they're plain text and easily exposed if accidentally committed to version control or shared insecurely. I designed and built this solution from the ground up to address that problem. The combination of **ChaCha20-Poly1305** for encryption, **PBKDF2-HMAC** for key derivation, and **BLAKE2s** for integrity verification ensures:

- **Speed**: ChaCha20-Poly1305 is optimized for performance on any device, including mobile and embedded systems
- **Security**: AEAD (Authenticated Encryption with Associated Data) protects against tampering, and PBKDF2 with 300,000 iterations makes brute-force attacks computationally expensive
- **Portability**: BLAKE2s provides fast, cryptographic hashing that works efficiently across platforms
- **Simplicity**: Easy-to-use CLI for developers who just want things to work

## Features

- 🔒 **Strong Encryption**: ChaCha20-Poly1305 AEAD cipher
- 🔑 **Key Derivation**: PBKDF2-HMAC-SHA256 with 300,000 iterations for password-based key generation
- ✅ **Integrity Verification**: BLAKE2s hashing prevents tampering with constant-time comparison
- 🚀 **Fast Performance**: Optimized for speed on any device
- 🛡️ **Defense Against Attacks**: Protection against brute-force, timing attacks, and data tampering
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

### Integrating Into Your Applications

**Example 1: Command-line argument for key**

```python
import argparse
from main import Getter

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='My Application')
    parser.add_argument('-k', '--key', required=True, help='Encryption key')
    parser.add_argument('-e', '--env-file', default='.env.compiled', help='Encrypted env file')
    args = parser.parse_args()
    
    # Load encrypted environment
    env_loader = Getter(args.env_file, args.key)
    
    if env_loader.env:
        # Your application logic here
        db_url = env_loader.env.get('DATABASE_URL')
        api_key = env_loader.env.get('API_KEY')
        print("Application started successfully!")
    else:
        print("Failed to load environment variables")
        exit(1)
```

Run your app:
```bash
python myapp.py -k mySecretKey123 -e config.env.compiled
```

**Example 2: Interactive key prompt**

```python
import getpass
from main import Getter

def main():
    env_file = input("Enter encrypted env file path: ")
    key = getpass.getpass("Enter encryption key: ")  # Hides input
    
    env_loader = Getter(env_file, key)
    
    if env_loader.env:
        # Use environment variables
        print("Environment loaded successfully!")
        # Your application logic
    else:
        print("Failed to decrypt environment")
        exit(1)

if __name__ == '__main__':
    main()
```

**Example 3: Auto-load into os.environ**

```python
from main import Getter
import os

# Load and automatically set environment variables
env_loader = Getter('.env.compiled', 'mySecretKey', env=True)

# Now you can use os.environ directly
database_url = os.environ.get('DATABASE_URL')
api_key = os.environ.get('API_KEY')
```

**Example 4: Environment variable for key (not recommended for production)**

```python
import os
from main import Getter

# Get key from environment variable
encryption_key = os.environ.get('APP_ENCRYPTION_KEY')

if not encryption_key:
    print("APP_ENCRYPTION_KEY environment variable not set")
    exit(1)

env_loader = Getter('.env.compiled', encryption_key)

if env_loader.env:
    # Your application continues
    pass
```

Run with:
```bash
export APP_ENCRYPTION_KEY="mySecretKey123"
python myapp.py
```

## File Format

### Input (.env file)
```
DATABASE_URL=postgresql://localhost/mydb
API_KEY=abc123xyz
SECRET_TOKEN=super_secret_value
```

### Output (.env.compiled)
Binary file structure (no versioning included - PoC simplification):
```
[4 bytes: cipher_len] [32 bytes: hash] [12 bytes: nonce] [16 bytes: tag] [variable: ciphertext]
```

**Note**: Production implementations would typically include a version byte/identifier at the beginning to support future algorithm upgrades and maintain backward compatibility.

## How It Works

1. **Encryption Process**:
   - Reads key-value pairs from environment file
   - Converts to JSON format
   - Generates random 12-byte nonce
   - Derives 32-byte encryption key from password using PBKDF2-HMAC-SHA256 (300,000 iterations) with the nonce as salt
   - Encrypts with ChaCha20-Poly1305 AEAD
   - Creates BLAKE2s integrity hash of encrypted data
   - Writes compiled binary file

2. **Decryption Process**:
   - Reads compiled file using memory mapping for efficiency
   - Extracts nonce and derives the same encryption key using PBKDF2-HMAC-SHA256
   - Verifies integrity hash using constant-time comparison (protects against timing attacks)
   - Decrypts using ChaCha20-Poly1305
   - Returns dictionary of environment variables or None if verification/decryption fails

## Security Notes & Proof of Concept Notice

**⚠️ IMPORTANT: This is a Proof of Concept (PoC) Level Implementation**

This tool is designed to introduce a secure environment encryption design pattern and is suitable for development use, but it has intentional simplifications that developers should be aware of:

### Current Security Implementation
- ✅ **Strong encryption**: ChaCha20-Poly1305 AEAD cipher
- ✅ **Key derivation**: PBKDF2-HMAC-SHA256 with 300,000 iterations
- ✅ **Integrity verification**: BLAKE2s with constant-time comparison
- ✅ **Protection against**: Brute-force attacks, timing attacks, data tampering

### Cryptographic Considerations
- ⚠️ **Nonce used as salt**: The implementation uses the encryption nonce as the PBKDF2 salt. This is intentional for simplicity and ensures that the same password doesn't produce the same derived key across different encryptions. However, for highest security standards, an independent random salt would typically be used.
- ⚠️ **No versioning**: This implementation does not include file format versioning. Production systems typically include version identifiers to allow for algorithm upgrades and backward compatibility. This was intentionally omitted to keep the PoC simple and focused on demonstrating the core encryption pattern.
- 📝 **Purpose**: The main goal is to introduce this design pattern for developers to understand and modify according to their needs, not to provide a production-grade implementation with every cryptographic best practice.

### Is This Secure?
**Yes, this is secure** for its intended use case - it uses proper encryption algorithms and protects your data. However, it doesn't meet *every* cryptographic requirement for the absolute highest possible safety standards used in critical production systems. 

**Why not production-ready?**
- No versioning means you can't easily upgrade encryption algorithms later
- Simplified salt strategy (nonce-as-salt) instead of independent salts
- Designed for demonstration and learning, not long-term maintenance

You can increase security and production-readiness by:
- Adding file format versioning (e.g., version byte at the start)
- Using a separate random salt instead of the nonce
- Increasing PBKDF2 iterations (though 300,000 is already strong)
- Adding key rotation mechanisms
- Implementing proper error handling and logging for production environments
- Adding additional layers of protection based on your threat model

### For Developers
- 🔧 **Modifiable**: Feel free to modify this code to meet your specific security requirements
- 📚 **Educational**: Use this as a learning tool and foundation for understanding encryption workflows
- 🛠️ **Customizable**: Adjust iterations, add versioning, change the salt strategy, or add additional security layers

### Best Practices
- Never commit your encryption keys/passwords to version control
- Store keys in secure key management systems (e.g., HashiCorp Vault, AWS Secrets Manager)
- The `.compiled` files are safe to commit but useless without the encryption key
- Evaluate your own threat model and adjust the implementation accordingly
- For production use, consider adding versioning and independent salt support

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

**GPL v3 with Special Exception**

This project is licensed under the GNU General Public License v3.0 (GPL v3).

### License Exception for Integration
If you use this code or include it as part of your web application, mobile app, or any other software project:

- ✅ **As a component/library**: You may use it under any license (unlicensed/permissive) if it's included as part of a larger application
- ⚠️ **As a standalone tool or creating derived env encryption libraries**: You **must** follow GPL v3 requirements

**In simple terms:**
- Including this in your app as one component among many? → Use freely under any license
- Building a new environment encryption tool based on this code? → Must be GPL v3
- Creating a library specifically for env encryption based on this? → Must be GPL v3

This exception allows developers to integrate the encryption functionality into their projects without viral GPL requirements, while ensuring that improvements to the core encryption tool itself remain open source.

## Author

**@hejhdiss (Muhammed Shafin P)**

Built with OpenSSL

## Contributing

This is my original design and implementation that I created after identifying the `.env` file security problem that many developers face online. I'm sharing it because I found my own solution to this issue and thought it might help others. Feel free to fork and adapt it for your use cases. If you find bugs or have suggestions, contributions are welcome!

## Disclaimer

This tool is provided as a proof-of-concept and educational resource for developers. The main purpose is to introduce this encryption design pattern, not to implement every possible cryptographic best practice. While it provides good security using industry-standard algorithms, some cryptographic requirements for the absolute highest possible safety are simplified for clarity and ease of understanding.

**This is secure for its intended use** - protecting development environment files - but developers working on critical production systems should evaluate their specific threat models and may want to enhance the implementation (such as using separate salts, adding HSM support, or implementing key rotation).

The code is designed to be understood, learned from, and modified. Feel free to adapt it to meet your organization's security requirements.