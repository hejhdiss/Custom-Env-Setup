


#include <openssl/evp.h>
#include <string.h>

#define KEY_SIZE   32
#define NONCE_SIZE 12
#define TAG_SIZE   16

#ifdef _WIN32
#define EXPORT __declspec(dllexport)
#else
#define EXPORT
#endif

EXPORT int chacha_encrypt(
    const unsigned char *plaintext,
    int plaintext_len,
    const unsigned char *key,
    const unsigned char *nonce,
    unsigned char *ciphertext,
    unsigned char *tag
) {
    EVP_CIPHER_CTX *ctx;
    int len, ciphertext_len;

    ctx = EVP_CIPHER_CTX_new();
    if (!ctx) return -1;

    if (!EVP_EncryptInit_ex(ctx, EVP_chacha20_poly1305(), NULL, NULL, NULL))
        goto error;

    if (!EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_AEAD_SET_IVLEN, NONCE_SIZE, NULL))
        goto error;

    if (!EVP_EncryptInit_ex(ctx, NULL, NULL, key, nonce))
        goto error;

    if (!EVP_EncryptUpdate(ctx, ciphertext, &len, plaintext, plaintext_len))
        goto error;

    ciphertext_len = len;

    if (!EVP_EncryptFinal_ex(ctx, ciphertext + len, &len))
        goto error;

    ciphertext_len += len;

    if (!EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_AEAD_GET_TAG, TAG_SIZE, tag))
        goto error;

    EVP_CIPHER_CTX_free(ctx);
    return ciphertext_len;

error:
    EVP_CIPHER_CTX_free(ctx);
    return -1;
}

EXPORT int chacha_decrypt(
    const unsigned char *ciphertext,
    int ciphertext_len,
    const unsigned char *tag,
    const unsigned char *key,
    const unsigned char *nonce,
    unsigned char *plaintext
) {
    EVP_CIPHER_CTX *ctx;
    int len, plaintext_len, ret;

    ctx = EVP_CIPHER_CTX_new();
    if (!ctx) return -1;

    if (!EVP_DecryptInit_ex(ctx, EVP_chacha20_poly1305(), NULL, NULL, NULL))
        goto error;

    if (!EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_AEAD_SET_IVLEN, NONCE_SIZE, NULL))
        goto error;

    if (!EVP_DecryptInit_ex(ctx, NULL, NULL, key, nonce))
        goto error;

    if (!EVP_DecryptUpdate(ctx, plaintext, &len, ciphertext, ciphertext_len))
        goto error;

    plaintext_len = len;

    if (!EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_AEAD_SET_TAG, TAG_SIZE, (void *)tag))
        goto error;

    ret = EVP_DecryptFinal_ex(ctx, plaintext + len, &len);
    EVP_CIPHER_CTX_free(ctx);

    if (ret <= 0) return -1;

    return plaintext_len + len;

error:
    EVP_CIPHER_CTX_free(ctx);
    return -1;
}
