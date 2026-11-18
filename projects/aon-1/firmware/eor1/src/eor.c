/* EOR-1 flight runtime: modes, deployment sequencer, authenticated commanding, store-and-forward, beacon, B-dot. */
#include "eor.h"
#include "sha256.h"
#include <string.h>
#include <math.h>
#include <stddef.h>

#define FRAM_STATE   0x0000u
#define STATE_MAGIC  0xA0E01001u
#define ARM_WINDOW_S 60u
#define CALM_RATE    0.02f          /* rad/s, about 1.1 deg/s: detumble done */
#define CALM_TICKS   600u           /* 60 s below CALM_RATE */
#define SAFE_BEACON_S 120u
static const float M_MAX[3] = {0.05f, 0.05f, 0.10f};   /* A m2: X/Y panel PCB coils, Z air coil on E07 */
#define BDOT_K       4.0e4f         /* A m2 s / T */

static uint32_t arm_time; static uint32_t calm_ticks;

/* ------------------------------------------------------------ small helpers */
uint16_t crc16_ccitt(const uint8_t *d, size_t n) {
    uint16_t c = 0xFFFF;
    while (n--) { c ^= (uint16_t)(*d++) << 8; for (int i = 0; i < 8; i++) c = (c & 0x8000) ? (uint16_t)((c << 1) ^ 0x1021) : (uint16_t)(c << 1); }
    return c;
}
static void be16(uint8_t *p, uint16_t v) { p[0] = (uint8_t)(v >> 8); p[1] = (uint8_t)v; }
static void be32(uint8_t *p, uint32_t v) { p[0] = (uint8_t)(v >> 24); p[1] = (uint8_t)(v >> 16); p[2] = (uint8_t)(v >> 8); p[3] = (uint8_t)v; }
static uint32_t rd32(const uint8_t *p) { return (uint32_t)p[0] << 24 | (uint32_t)p[1] << 16 | (uint32_t)p[2] << 8 | p[3]; }
static uint16_t tm_seq;

static void ccsds_hdr(uint8_t *h, int tc, uint16_t apid, uint16_t seq, size_t total) {
    be16(h, (uint16_t)((tc ? 0x1000 : 0x0000) | (apid & 0x7FF)));
    be16(h + 2, (uint16_t)(0xC000 | (seq & 0x3FFF)));
    be16(h + 4, (uint16_t)(total - 7));
}
static size_t tm_close(uint8_t *f, size_t n) { uint16_t c = crc16_ccitt(f, n); be16(f + n, c); n += 2; be16(f + 4, (uint16_t)(n - 7)); return n; }

size_t tc_build(const uint8_t key[32], uint32_t seq, uint8_t cmd, const uint8_t *args, size_t an, uint8_t *out) {
    size_t n = 6; uint8_t mac[32];
    out[n++] = cmd; if (an) memcpy(out + n, args, an); n += an;
    be32(out + n, seq); n += 4;
    ccsds_hdr(out, 1, APID_TC, (uint16_t)seq, n + MAC_LEN);
    hmac_sha256(key, 32, out, n, mac); memcpy(out + n, mac, MAC_LEN);
    return n + MAC_LEN;
}

/* ------------------------------------------------------------ persistence */
typedef struct { uint32_t magic; eor_t s; uint16_t crc; } stored_t;
static void persist(const eor_t *s) {
    stored_t st; memset(&st, 0, sizeof st); st.magic = STATE_MAGIC; st.s = *s; memset(st.s.key, 0, 32);   /* key lives in its own write-protected FRAM block */
    st.crc = crc16_ccitt((const uint8_t *)&st, offsetof(stored_t, crc));
    hal_fram_write(FRAM_STATE, &st, sizeof st);
}

void eor_init(eor_t *s, const uint8_t key[32]) {
    stored_t st;
    memset(s, 0, sizeof *s);
    if (hal_fram_read(FRAM_STATE, &st, sizeof st) == 0 && st.magic == STATE_MAGIC &&
        st.crc == crc16_ccitt((const uint8_t *)&st, offsetof(stored_t, crc))) {
        *s = st.s;
        s->burning = 0; s->burn_until_ms = 0; s->deploy_armed = 0; s->b_valid = 0;
    } else {
        s->tx_enabled = 1;
    }
    memcpy(s->key, key, 32);
    s->mode = M_BOOT;
    s->boot_count++;
    for (int i = 0; i < LOAD_N; i++) hal_load(i, 0);
    hal_burn(0, 0); hal_burn(1, 0); hal_pa_enable(0);
    calm_ticks = 0;
    persist(s);
}

/* ------------------------------------------------------------ B-dot */
void bdot(const float b[3], const float bp[3], float dt, float m[3]) {
    for (int i = 0; i < 3; i++) {
        float d = (b[i] - bp[i]) * 1e-9f / dt;     /* T/s */
        float v = -BDOT_K * d;
        m[i] = v > M_MAX[i] ? M_MAX[i] : (v < -M_MAX[i] ? -M_MAX[i] : v);
    }
}

/* ------------------------------------------------------------ store and forward */
static uint32_t slot_addr(uint32_t i) { return SF_BASE + (i % SF_SLOTS) * SF_SLOT; }
int sf_store(eor_t *s, const uint8_t *msg, size_t n, uint32_t *id) {
    uint8_t slot[SF_SLOT];
    if (n == 0 || n > SF_MSG_MAX) return ERR_FORMAT;
    if (s->sf_count >= SF_SLOTS - 16u) return ERR_FULL;           /* one sector always free so an erase never hits live data */
    uint32_t i = s->sf_head;
    if ((i % 16u) == 0) hal_nor_erase4k(slot_addr(i));
    memset(slot, 0xFF, sizeof slot);
    slot[0] = 0xA5; be16(slot + 1, (uint16_t)n); be32(slot + 3, s->sf_next_id); slot[7] = 0;
    memcpy(slot + 12, msg, n);
    be16(slot + 8, crc16_ccitt(slot + 12, n)); slot[10] = slot[11] = 0;
    hal_nor_write(slot_addr(i), slot, 12 + n);
    if (id) *id = s->sf_next_id;
    s->sf_next_id++; s->sf_head = (i + 1) % SF_SLOTS; s->sf_count++;
    return ACK_OK;
}
int sf_fetch(eor_t *s, uint32_t id, uint8_t *msg, size_t *n) {
    uint8_t h[12];
    for (uint32_t k = 0; k < s->sf_count; k++) {
        uint32_t a = slot_addr(s->sf_tail + k);
        hal_nor_read(a, h, 12);
        if (h[0] != 0xA5 || rd32(h + 3) != id) continue;
        size_t L = (size_t)h[1] << 8 | h[2];
        if (L > SF_MSG_MAX) return ERR_NOTFOUND;
        hal_nor_read(a + 12, msg, L);
        if (crc16_ccitt(msg, L) != ((uint16_t)h[8] << 8 | h[9])) return ERR_NOTFOUND;
        *n = L; return ACK_OK;
    }
    return ERR_NOTFOUND;
}
int sf_delete_oldest(eor_t *s) {
    if (!s->sf_count) return ERR_NOTFOUND;
    s->sf_tail = (s->sf_tail + 1) % SF_SLOTS; s->sf_count--; return ACK_OK;
}

/* ------------------------------------------------------------ telemetry */
size_t eor_hk(const eor_t *s, uint8_t *f) {
    hal_power_t p; hal_power(&p);
    size_t n = 6;
    f[n++] = 0x01;                                  /* HK type 1 */
    memcpy(f + n, "AON1", 4); n += 4;
    f[n++] = (uint8_t)s->mode;
    be32(f + n, hal_rtc_s()); n += 4;
    be16(f + n, (uint16_t)(p.vbatt * 1000.0f)); n += 2;
    be16(f + n, (uint16_t)(int16_t)(p.ibatt * 1000.0f)); n += 2;
    be16(f + n, (uint16_t)(int16_t)(p.tbatt_c * 10.0f)); n += 2;
    be16(f + n, (uint16_t)(int16_t)(p.tobc_c * 10.0f)); n += 2;
    for (int i = 0; i < 4; i++) { be16(f + n, (uint16_t)(p.isolar[i] * 1000.0f)); n += 2; }
    be32(f + n, s->boot_count); n += 4;
    be16(f + n, (uint16_t)s->safe_count); n += 2;
    be32(f + n, s->rx_ok); n += 4;
    be16(f + n, (uint16_t)s->rx_bad_auth); n += 2;
    be32(f + n, s->sf_count); n += 4;
    f[n++] = (uint8_t)(s->deployed[0] | s->deployed[1] << 1 | s->heater_on << 2 | s->tx_enabled << 3);
    ccsds_hdr(f, 0, APID_TM_HK, tm_seq++, n + 2);
    return tm_close(f, n);
}

static size_t ack(uint8_t *r, uint8_t cmd, uint8_t st, const uint8_t *d, size_t dn) {
    size_t n = 6; r[n++] = cmd; r[n++] = st; if (dn) memcpy(r + n, d, dn); n += dn;
    ccsds_hdr(r, 0, APID_TM_ACK, tm_seq++, n + 2);
    return tm_close(r, n);
}

static int rf_allowed(const eor_t *s) { return hal_rtc_s() >= T_RF_S && s->tx_enabled; }

/* ------------------------------------------------------------ commands */
int eor_handle_tc(eor_t *s, const uint8_t *f, size_t n, uint8_t *r, size_t *rn) {
    uint8_t mac[32]; *rn = 0;
    if (n < 6 + 1 + 4 + MAC_LEN || n > MAX_FRAME) { return -ERR_FORMAT; }
    uint16_t w0 = (uint16_t)(f[0] << 8 | f[1]);
    if ((w0 & 0xE000) != 0 || !(w0 & 0x1000) || (w0 & 0x7FF) != APID_TC || (size_t)((f[4] << 8 | f[5]) + 7) != n) return -ERR_FORMAT;
    hmac_sha256(s->key, 32, f, n - MAC_LEN, mac);
    if (!ct_equal(mac, f + n - MAC_LEN, MAC_LEN)) { s->rx_bad_auth++; return -ERR_AUTH; }   /* silent: no oracle for forgers */
    uint32_t seq = rd32(f + n - MAC_LEN - 4);
    if (seq <= s->tc_seq) { s->rx_replay++; return -ERR_REPLAY; }
    s->tc_seq = seq; s->rx_ok++;
    uint8_t cmd = f[6]; const uint8_t *a = f + 7; size_t an = n - 7 - 4 - MAC_LEN;
    uint8_t st = ACK_OK, d[SF_SLOT]; size_t dn = 0; uint32_t t = hal_rtc_s();
    switch (cmd) {
    case CMD_PING: break;
    case CMD_GET_HK: *rn = eor_hk(s, r); persist(s); return 0;
    case CMD_SET_MODE:
        if (an != 1) { st = ERR_FORMAT; break; }
        if (t < T_RF_S || (a[0] != M_DETUMBLE && a[0] != M_NOMINAL && a[0] != M_SAFE)) { st = ERR_STATE; break; }
        s->mode = (eor_mode_t)a[0]; if (s->mode == M_SAFE) s->safe_count++;
        break;
    case CMD_SF_STORE: { uint32_t id; st = (uint8_t)sf_store(s, a, an, &id); if (st == ACK_OK) { be32(d, id); dn = 4; } break; }
    case CMD_SF_FETCH: {
        if (an != 4) { st = ERR_FORMAT; break; }
        size_t L = 0; st = (uint8_t)sf_fetch(s, rd32(a), d + 4, &L);
        if (st == ACK_OK) { memcpy(d, a, 4); dn = 4 + L; }
        break; }
    case CMD_SF_DELETE: st = (uint8_t)sf_delete_oldest(s); break;
    case CMD_SF_COUNT: be32(d, s->sf_count); dn = 4; break;
    case CMD_DEPLOY_ARM: s->deploy_armed = 1; arm_time = t; break;
    case CMD_DEPLOY_FIRE:                                  /* two-step: ARM then FIRE within 60 s, never before 30 min */
        if (an != 1 || a[0] > 1) { st = ERR_FORMAT; break; }
        if (!s->deploy_armed || t - arm_time > ARM_WINDOW_S || t < T_ANTENNA_S) { st = ERR_STATE; s->deploy_armed = 0; break; }
        s->deploy_armed = 0; s->burn_tries[a[0]] = 0; s->deployed[a[0]] = 0; s->last_burn_s = 0;
        s->mode = M_DEPLOY; break;
    case CMD_SET_TIME: if (an != 4) { st = ERR_FORMAT; break; } hal_rtc_set(rd32(a)); break;
    case CMD_TX_ENABLE: if (an != 1) { st = ERR_FORMAT; break; } s->tx_enabled = a[0] ? 1 : 0; if (!s->tx_enabled) hal_pa_enable(0); break;
    default: st = ERR_FORMAT;
    }
    persist(s);
    *rn = ack(r, cmd, st, d, dn);
    return st;
}

/* ------------------------------------------------------------ the 100 ms tick */
static void burn_start(eor_t *s, int e, uint32_t t) {
    hal_load(LOAD_BURN, 1); hal_burn(e, 1);
    s->burning = (int8_t)(e + 1); s->burn_until_ms = hal_ms() + BURN_ON_MS; s->burn_tries[e]++; s->last_burn_s = t;
}

void eor_tick(eor_t *s) {
    hal_power_t p; uint32_t t = hal_rtc_s(), now = hal_ms();
    hal_wdt_kick();
    hal_power(&p);

    if (s->burning && (int32_t)(now - s->burn_until_ms) >= 0) { hal_burn(s->burning - 1, 0); hal_load(LOAD_BURN, 0); s->burning = 0; }

    /* battery heater thermostat: hysteresis, never below critical voltage */
    if (p.tbatt_c < T_HEAT_ON_C && p.vbatt > V_CRIT) s->heater_on = 1;
    if (p.tbatt_c > T_HEAT_OFF_C || p.vbatt <= V_CRIT) s->heater_on = 0;
    hal_load(LOAD_HEATER, s->heater_on);

    for (int e = 0; e < 2; e++) if (!s->deployed[e] && hal_antenna_deployed(e)) s->deployed[e] = 1;
    int deploy_done = (s->deployed[0] || s->burn_tries[0] >= BURN_RETRIES) && (s->deployed[1] || s->burn_tries[1] >= BURN_RETRIES);

    switch (s->mode) {
    case M_BOOT:
        s->mode = t < T_ANTENNA_S ? M_WAIT_DEPLOY : (!deploy_done ? M_DEPLOY : (t < T_RF_S ? M_WAIT_RF : M_DETUMBLE));
        break;
    case M_WAIT_DEPLOY:
        if (t >= T_ANTENNA_S) s->mode = M_DEPLOY;
        break;
    case M_DEPLOY:
        if (!s->burning && p.vbatt > V_SAFE_ENTER) {
            for (int e = 0; e < 2; e++) {
                if (s->deployed[e] || s->burn_tries[e] >= BURN_RETRIES) continue;
                if (s->burn_tries[e] == 0 || t - s->last_burn_s >= BURN_RETRY_S) { burn_start(s, e, t); break; }
            }
        }
        if (deploy_done && !s->burning) s->mode = t < T_RF_S ? M_WAIT_RF : M_DETUMBLE;
        break;
    case M_WAIT_RF:
        if (t >= T_RF_S) s->mode = M_DETUMBLE;
        break;
    case M_DETUMBLE: case M_NOMINAL: case M_SAFE: default:
        break;
    }

    int after_rf = t >= T_RF_S && (s->mode == M_DETUMBLE || s->mode == M_NOMINAL || s->mode == M_SAFE);
    if (after_rf && s->mode != M_SAFE && p.vbatt < V_SAFE_ENTER) { s->mode = M_SAFE; s->safe_count++; }
    if (s->mode == M_SAFE && p.vbatt > V_SAFE_EXIT) s->mode = M_NOMINAL;

    /* loads by mode */
    hal_load(LOAD_COM, after_rf && p.vbatt > V_CRIT);
    hal_load(LOAD_ADCS, after_rf && s->mode != M_SAFE);
    hal_load(LOAD_PAYLOAD, s->mode == M_NOMINAL);
    hal_pa_enable(after_rf && rf_allowed(s) && p.vbatt > V_CRIT);

    /* attitude: B-dot in DETUMBLE (and NOMINAL keeps it running at low gain via the same law) */
    if (after_rf && s->mode != M_SAFE) {
        float b[3], m[3] = {0, 0, 0}; hal_mag(b);
        if (s->b_valid) {
            float dt = (float)(now - s->b_prev_ms) / 1000.0f;
            if (dt > 0.05f) {
                bdot(b, s->b_prev, dt, m);
                float db = 0, bn = 0;
                for (int i = 0; i < 3; i++) { float d = b[i] - s->b_prev[i]; db += d * d; bn += b[i] * b[i]; }
                float rate = bn > 0 ? sqrtf(db / bn) / dt : 0;
                calm_ticks = rate < CALM_RATE ? calm_ticks + 1 : 0;
                if (s->mode == M_DETUMBLE && calm_ticks >= CALM_TICKS) s->mode = M_NOMINAL;
            }
        }
        hal_torquer(m);
        memcpy(s->b_prev, b, sizeof b); s->b_prev_ms = now; s->b_valid = 1;
    } else {
        const float z[3] = {0, 0, 0}; hal_torquer(z); s->b_valid = 0;
    }

    /* receive and answer */
    uint8_t rx[MAX_FRAME], tx[MAX_FRAME + 16]; int n;
    while ((n = hal_radio_rx(rx, sizeof rx)) > 0) {
        size_t rn = 0;
        eor_handle_tc(s, rx, (size_t)n, tx, &rn);
        if (rn && rf_allowed(s)) { hal_radio_tx(tx, rn); s->tx_frames++; }
    }

    /* beacon */
    uint32_t period = s->mode == M_SAFE ? SAFE_BEACON_S : BEACON_S;
    if (after_rf && rf_allowed(s) && t - s->last_beacon_s >= period) {
        size_t bn = eor_hk(s, tx); hal_radio_tx(tx, bn); s->tx_frames++; s->last_beacon_s = t;
    }
    persist(s);
}
