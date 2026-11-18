/* Host simulator for EOR-1: time, FRAM, NOR, loads, radio queue and a tumbling magnetic field. */
#include "hal_sim.h"
#include <string.h>
#include <math.h>

sim_t SIM;
static uint8_t fram[32768];
static uint8_t nor[SF_BASE + SF_SLOTS * SF_SLOT];

void sim_reset(int keep_nv) {
    if (!keep_nv) { memset(fram, 0xFF, sizeof fram); memset(nor, 0xFF, sizeof nor); }
    uint32_t keep_t = SIM.rtc_s;
    memset(&SIM, 0, sizeof SIM);
    if (keep_nv) SIM.rtc_s = keep_t;
    SIM.p.vbatt = 7.8f; SIM.p.tbatt_c = 15.0f; SIM.p.tobc_c = 20.0f;
    SIM.rate = 0.15f;                                   /* rad/s tumble after separation */
}
void sim_advance_ms(uint32_t ms) { SIM.ms += ms; SIM.acc += ms; while (SIM.acc >= 1000) { SIM.acc -= 1000; SIM.rtc_s++; }
    /* antenna releases after the burn has been on for 3 s, unless the test jams it */
    for (int e = 0; e < 2; e++) if (SIM.burn[e]) { SIM.burn_ms[e] += ms; if (SIM.burn_ms[e] >= 3000 && !SIM.jam[e]) SIM.released[e] = 1; }
    /* torquer damps the tumble: crude but monotonic, proportional to |m| */
    float m = fabsf(SIM.m[0]) + fabsf(SIM.m[1]) + fabsf(SIM.m[2]);
    SIM.rate -= SIM.rate * m * 0.004f * (float)ms / 100.0f; if (SIM.rate < 0.001f) SIM.rate = 0.001f;
    SIM.angle += SIM.rate * (float)ms / 1000.0f;
}
uint32_t hal_ms(void) { return SIM.ms; }
uint32_t hal_rtc_s(void) { return SIM.rtc_s; }
void hal_rtc_set(uint32_t s) { SIM.rtc_s = s; }
void hal_wdt_kick(void) { SIM.wdt_kicks++; }
int hal_fram_read(uint32_t a, void *d, size_t n) { if (a + n > sizeof fram) return -1; memcpy(d, fram + a, n); return 0; }
int hal_fram_write(uint32_t a, const void *d, size_t n) { if (a + n > sizeof fram) return -1; memcpy(fram + a, d, n); return 0; }
int hal_nor_read(uint32_t a, void *d, size_t n) { if (a + n > sizeof nor) return -1; memcpy(d, nor + a, n); return 0; }
int hal_nor_write(uint32_t a, const void *d, size_t n) { if (a + n > sizeof nor) return -1; const uint8_t *s = d; for (size_t i = 0; i < n; i++) nor[a + i] &= s[i]; return 0; }
int hal_nor_erase4k(uint32_t a) { a &= ~0xFFFu; if (a + 4096 > sizeof nor) return -1; memset(nor + a, 0xFF, 4096); SIM.erases++; return 0; }
void hal_load(int l, int on) { SIM.load[l] = on; }
void hal_burn(int e, int on) { if (on && !SIM.load[LOAD_BURN]) return; SIM.burn[e] = on; if (on) { SIM.burn_count[e]++; SIM.burn_ms[e] = 0; if (SIM.rtc_s < SIM.first_burn_s || !SIM.first_burn_s) SIM.first_burn_s = SIM.rtc_s; } }
int hal_antenna_deployed(int e) { return SIM.released[e]; }
void hal_pa_enable(int on) { SIM.pa = on; }
void hal_power(hal_power_t *p) { *p = SIM.p; }
void hal_mag(float b[3]) { float B = 30000.0f; b[0] = B * cosf(SIM.angle); b[1] = B * sinf(SIM.angle) * 0.8f; b[2] = B * 0.6f * sinf(SIM.angle * 0.7f); }
void hal_torquer(const float m[3]) { memcpy(SIM.m, m, sizeof SIM.m); }
int hal_radio_rx(uint8_t *b, size_t max) { if (!SIM.rx_len) return 0; size_t n = SIM.rx_len < max ? SIM.rx_len : max; memcpy(b, SIM.rx, n); SIM.rx_len = 0; return (int)n; }
int hal_radio_tx(const uint8_t *b, size_t n) {
    if (!SIM.pa || !SIM.load[LOAD_COM]) { SIM.tx_violation++; return -1; }
    if (!SIM.first_tx_s) SIM.first_tx_s = SIM.rtc_s ? SIM.rtc_s : 1;
    memcpy(SIM.tx, b, n); SIM.tx_len = n; SIM.tx_count++; return (int)n;
}
