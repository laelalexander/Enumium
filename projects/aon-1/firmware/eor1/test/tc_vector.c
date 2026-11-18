/* prints a TC frame (hex) for the Python ground tool's interop test */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../src/eor.h"
int main(int argc, char **argv) {
    uint8_t key[32]; for (int i = 0; i < 32; i++) key[i] = (uint8_t)(i + 1);
    uint32_t seq = (uint32_t)strtoul(argv[1], 0, 10); uint8_t cmd = (uint8_t)atoi(argv[2]);
    const char *a = argc > 3 ? argv[3] : ""; uint8_t f[256];
    size_t n = tc_build(key, seq, cmd, (const uint8_t *)a, strlen(a), f);
    for (size_t i = 0; i < n; i++) printf("%02x", f[i]); printf("\n"); return 0;
}
