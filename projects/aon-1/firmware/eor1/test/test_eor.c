/* EOR-1 host tests: crypto vectors, timeline/inhibits, deployment retries, authentication, safe mode, store-and-forward, persistence. */
#include <stdio.h>
#include <string.h>
#include <math.h>
#include "hal_sim.h"
#include "../src/sha256.h"

static int fails, checks;
#define CHECK(c, ...) do { checks++; if (!(c)) { fails++; printf("FAIL %s:%d: ", __FILE__, __LINE__); printf(__VA_ARGS__); printf("\n"); } } while (0)
static const uint8_t KEY[32] = {1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32};
static uint32_t seq = 100;

static void hex(const char *h, uint8_t *o) { for (size_t i = 0; i < strlen(h) / 2; i++) sscanf(h + 2 * i, "%2hhx", &o[i]); }
static void run_s(eor_t *s, uint32_t secs) { for (uint32_t i = 0; i < secs * 10; i++) { sim_advance_ms(100); eor_tick(s); } }
static int send(eor_t *s, uint8_t cmd, const uint8_t *a, size_t an, uint8_t *resp, size_t *rn) {
    uint8_t f[256]; size_t n = tc_build(KEY, ++seq, cmd, a, an, f); return eor_handle_tc(s, f, n, resp, rn);
}

static void t_crypto(void) {
    uint8_t d[32], e[32];
    sha256((const uint8_t *)"abc", 3, d); hex("ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad", e);
    CHECK(!memcmp(d, e, 32), "sha256(abc)");
    hmac_sha256((const uint8_t *)"Jefe", 4, (const uint8_t *)"what do ya want for nothing?", 28, d);
    hex("5bdcc146bf60754e6a042426089575c75a003f089d2739839dec58b964ec3843", e);
    CHECK(!memcmp(d, e, 32), "HMAC RFC 4231 case 2");
    uint8_t m[1000]; memset(m, 'a', sizeof m); sha256(m, sizeof m, d);
    hex("41edece42d63e8d9bf515a9ba6932e1c20cbc9f5a5d134645adb5db1b9737ea3", e);
    CHECK(!memcmp(d, e, 32), "sha256 of 1000 x 'a' (multi-block)");
    CHECK(crc16_ccitt((const uint8_t *)"123456789", 9) == 0x29B1, "CRC-16/CCITT-FALSE check value");
}

static void t_timeline(void) {
    eor_t s; sim_reset(0); eor_init(&s, KEY);
    run_s(&s, T_ANTENNA_S - 1);
    CHECK(SIM.burn_count[0] == 0 && SIM.burn_count[1] == 0, "no burn before 30 min");
    CHECK(SIM.tx_count == 0 && !SIM.pa && !SIM.load[LOAD_COM], "radio dark before 30 min");
    run_s(&s, 60);
    CHECK(SIM.first_burn_s >= T_ANTENNA_S, "first burn at/after 30 min (t=%u)", SIM.first_burn_s);
    CHECK(s.deployed[0] && s.deployed[1], "both elements released");
    CHECK(s.mode == M_WAIT_RF, "waits for RF time, mode %d", s.mode);
    run_s(&s, T_RF_S - T_ANTENNA_S - 120);
    CHECK(SIM.tx_count == 0, "no RF before 45 min");
    run_s(&s, 200);
    CHECK(SIM.first_tx_s >= T_RF_S, "first transmission at/after 45 min (t=%u)", SIM.first_tx_s);
    CHECK(SIM.tx_violation == 0, "never transmitted with the PA or COM load off");
    CHECK(s.mode == M_DETUMBLE || s.mode == M_NOMINAL, "detumbling after RF");
    run_s(&s, 3 * 3600);
    CHECK(s.mode == M_NOMINAL, "detumble completes into NOMINAL (rate %.4f rad/s)", SIM.rate);
    uint32_t b = SIM.tx_count; run_s(&s, 300);
    CHECK(SIM.tx_count - b >= 9 && SIM.tx_count - b <= 11, "beacon every 30 s (%u in 300 s)", SIM.tx_count - b);
    CHECK(SIM.wdt_kicks > 0, "watchdog kicked");
}

static void t_jammed(void) {
    eor_t s; sim_reset(0); SIM.jam[1] = 1; eor_init(&s, KEY);
    run_s(&s, T_ANTENNA_S + 4 * BURN_RETRY_S + 120);
    CHECK(SIM.burn_count[0] == 1, "element 0 burned once (%u)", SIM.burn_count[0]);
    CHECK(SIM.burn_count[1] == BURN_RETRIES, "jammed element retried %u times (%u)", BURN_RETRIES, SIM.burn_count[1]);
    CHECK(s.mode != M_DEPLOY, "sequencer gives up and continues (mode %d)", s.mode);
    /* ground can re-fire after diagnosis: two-step */
    uint8_t r[300]; size_t rn; uint8_t e = 1;
    SIM.jam[1] = 0;
    CHECK(send(&s, CMD_DEPLOY_FIRE, &e, 1, r, &rn) == ERR_STATE, "FIRE without ARM is refused");
    CHECK(send(&s, CMD_DEPLOY_ARM, 0, 0, r, &rn) == ACK_OK, "ARM accepted");
    CHECK(send(&s, CMD_DEPLOY_FIRE, &e, 1, r, &rn) == ACK_OK, "FIRE after ARM accepted");
    run_s(&s, 30);
    CHECK(s.deployed[1], "element 1 released on the commanded burn");
}

static void t_auth(void) {
    eor_t s; sim_reset(0); eor_init(&s, KEY); SIM.rtc_s = T_RF_S + 10; s.deployed[0] = s.deployed[1] = 1;
    uint8_t f[256], r[300]; size_t n, rn;
    n = tc_build(KEY, 500, CMD_PING, 0, 0, f);
    CHECK(eor_handle_tc(&s, f, n, r, &rn) == ACK_OK && rn > 0, "valid PING acknowledged");
    CHECK(r[6] == CMD_PING && r[7] == ACK_OK, "ACK echoes the command with status OK");
    CHECK(eor_handle_tc(&s, f, n, r, &rn) == -ERR_REPLAY && rn == 0, "replayed frame rejected silently");
    n = tc_build(KEY, 499, CMD_PING, 0, 0, f);
    CHECK(eor_handle_tc(&s, f, n, r, &rn) == -ERR_REPLAY, "older sequence rejected");
    uint8_t bad[32]; memcpy(bad, KEY, 32); bad[0] ^= 1;
    n = tc_build(bad, 900, CMD_PING, 0, 0, f);
    CHECK(eor_handle_tc(&s, f, n, r, &rn) == -ERR_AUTH && rn == 0, "wrong key rejected silently");
    n = tc_build(KEY, 901, CMD_SET_MODE, (const uint8_t *)"\x06", 1, f); f[7] ^= 0x01;
    CHECK(eor_handle_tc(&s, f, n, r, &rn) == -ERR_AUTH, "bit flip in the arguments rejected");
    CHECK(s.rx_bad_auth == 2 && s.rx_replay == 2, "counters (bad %u replay %u)", s.rx_bad_auth, s.rx_replay);
    CHECK(eor_handle_tc(&s, f, 10, r, &rn) == -ERR_FORMAT, "short frame rejected");
    n = tc_build(KEY, 902, CMD_PING, 0, 0, f); eor_handle_tc(&s, f, n, r, &rn); uint16_t c = crc16_ccitt(r, rn - 2);
    CHECK(c == (uint16_t)(r[rn - 2] << 8 | r[rn - 1]), "TM CRC valid");
}

static void t_safe(void) {
    eor_t s; sim_reset(0); eor_init(&s, KEY); run_s(&s, T_RF_S + 60);
    SIM.p.vbatt = 6.7f; run_s(&s, 1);
    CHECK(s.mode == M_SAFE && !SIM.load[LOAD_ADCS] && !SIM.load[LOAD_PAYLOAD], "low battery -> SAFE, ADCS and payload off");
    CHECK(SIM.load[LOAD_COM], "receiver stays on in SAFE");
    uint32_t b = SIM.tx_count; run_s(&s, 600);
    CHECK(SIM.tx_count - b <= 6, "SAFE beacon slowed to 120 s (%u in 600 s)", SIM.tx_count - b);
    SIM.p.vbatt = 7.2f; run_s(&s, 5); CHECK(s.mode == M_SAFE, "hysteresis: stays SAFE at 7.2 V");
    SIM.p.vbatt = 7.5f; run_s(&s, 1); CHECK(s.mode == M_NOMINAL, "recovers above 7.4 V");
    SIM.p.tbatt_c = 0.0f; run_s(&s, 1); CHECK(SIM.load[LOAD_HEATER], "heater on below 2 °C");
    SIM.p.tbatt_c = 5.0f; run_s(&s, 1); CHECK(SIM.load[LOAD_HEATER], "heater holds between 2 and 8 °C");
    SIM.p.tbatt_c = 9.0f; run_s(&s, 1); CHECK(!SIM.load[LOAD_HEATER], "heater off above 8 °C");
    uint8_t r[300]; size_t rn; uint8_t z = 0;
    send(&s, CMD_TX_ENABLE, &z, 1, r, &rn); b = SIM.tx_count; run_s(&s, 300);
    CHECK(SIM.tx_count == b && !SIM.pa, "ground TX disable silences the satellite");
}

static void t_sf(void) {
    eor_t s; sim_reset(0); eor_init(&s, KEY); SIM.rtc_s = T_RF_S + 10;
    uint8_t r[300], m[SF_MSG_MAX]; size_t rn, n; uint32_t id;
    for (int i = 0; i < 3; i++) { char t[32]; int L = snprintf(t, sizeof t, "hello node %d", i); CHECK(send(&s, CMD_SF_STORE, (uint8_t *)t, (size_t)L, r, &rn) == ACK_OK, "store %d", i); }
    CHECK(sf_fetch(&s, 1, m, &n) == ACK_OK && n == 12 && !memcmp(m, "hello node 1", 12), "fetch by id");
    uint8_t idb[4] = {0, 0, 0, 2};
    CHECK(send(&s, CMD_SF_FETCH, idb, 4, r, &rn) == ACK_OK && !memcmp(r + 12, "hello node 2", 12), "fetch over the link");
    CHECK(sf_delete_oldest(&s) == ACK_OK && sf_fetch(&s, 0, m, &n) == ERR_NOTFOUND, "delete oldest");
    uint8_t big[SF_MSG_MAX + 1]; memset(big, 7, sizeof big);
    CHECK(sf_store(&s, big, sizeof big, &id) == ERR_FORMAT, "oversize refused");
    int st = ACK_OK; uint32_t k = 0;
    while (st == ACK_OK) { st = sf_store(&s, big, SF_MSG_MAX, &id); k++; }
    CHECK(st == ERR_FULL && s.sf_count == SF_SLOTS - 16, "queue fills to %u then refuses (count %u)", SF_SLOTS - 16, s.sf_count);
    for (int i = 0; i < 100; i++) sf_delete_oldest(&s);
    for (int i = 0; i < 90; i++) CHECK(sf_store(&s, (const uint8_t *)"wrap", 4, &id) == ACK_OK, "store after wrap");
    CHECK(sf_fetch(&s, id, m, &n) == ACK_OK && n == 4 && !memcmp(m, "wrap", 4), "wrapped slot reads back (id %u)", id);
}

static void t_reboot(void) {
    eor_t s; sim_reset(0); eor_init(&s, KEY); run_s(&s, T_RF_S + 300);
    uint32_t burns = SIM.burn_count[0] + SIM.burn_count[1], seqb = s.tc_seq;
    uint8_t r[300]; size_t rn; send(&s, CMD_PING, 0, 0, r, &rn);
    sim_reset(1); SIM.released[0] = SIM.released[1] = 1;      /* reset: RAM lost, FRAM and RTC kept */
    eor_t s2; eor_init(&s2, KEY);
    CHECK(s2.boot_count == 2, "boot count persisted (%u)", s2.boot_count);
    CHECK(s2.deployed[0] && s2.deployed[1] && s2.tc_seq > seqb, "deploy flags and command sequence persisted");
    run_s(&s2, 120);
    CHECK(SIM.burn_count[0] + SIM.burn_count[1] == 0 && burns == 2, "no re-burn after a reset");
    CHECK(s2.mode == M_DETUMBLE || s2.mode == M_NOMINAL, "resumes after RF time (mode %d)", s2.mode);
}

static void t_bdot(void) {
    float b0[3] = {20000, 0, 0}, b1[3] = {19000, 1000, -500}, m[3];
    bdot(b1, b0, 0.1f, m);
    CHECK(m[0] > 0 && m[1] < 0 && m[2] > 0, "B-dot opposes dB/dt");
    CHECK(fabsf(m[0]) <= 0.05f && fabsf(m[2]) <= 0.10f, "dipole saturates at the coil limits");
}

int main(void) {
    t_crypto(); t_timeline(); t_jammed(); t_auth(); t_safe(); t_sf(); t_reboot(); t_bdot();
    printf("%d checks, %d failed\n", checks, fails);
    return fails ? 1 : 0;
}
