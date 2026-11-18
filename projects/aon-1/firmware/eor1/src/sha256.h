/* SHA-256 and HMAC-SHA256 (FIPS 180-4, RFC 2104). Small, no allocation. */
#ifndef EOR_SHA256_H
#define EOR_SHA256_H
#include <stdint.h>
#include <stddef.h>
typedef struct { uint32_t h[8]; uint64_t len; uint8_t buf[64]; size_t n; } sha256_ctx;
void sha256_init(sha256_ctx *c);
void sha256_update(sha256_ctx *c, const uint8_t *d, size_t n);
void sha256_final(sha256_ctx *c, uint8_t out[32]);
void sha256(const uint8_t *d, size_t n, uint8_t out[32]);
void hmac_sha256(const uint8_t *key, size_t klen, const uint8_t *msg, size_t mlen, uint8_t out[32]);
int  ct_equal(const uint8_t *a, const uint8_t *b, size_t n);   /* constant time compare, 1 = equal */
#endif
