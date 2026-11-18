/* EOR-1: the AON-1 flight runtime. Single-threaded superloop, 100 ms tick, all state in eor_t (mirrored to FRAM). */
#ifndef EOR_H
#define EOR_H
#include <stdint.h>
#include <stddef.h>
#include "hal.h"

/* ---- timeline (AON dispenser ICD / CDS rev 14.1) */
#define T_ANTENNA_S      (30u * 60u)    /* no deployable motion before 30 min after separation */
#define T_RF_S           (45u * 60u)    /* no RF before 45 min */
#define BURN_ON_MS       6000u
#define BURN_RETRIES     4u
#define BURN_RETRY_S     (10u * 60u)
#define BEACON_S         30u

/* ---- power thresholds (2S Li-ion) */
#define V_SAFE_ENTER     6.80f
#define V_SAFE_EXIT      7.40f
#define V_CRIT           6.20f          /* below: everything off except OBC and receiver */
#define T_HEAT_ON_C      2.0f
#define T_HEAT_OFF_C     8.0f

typedef enum { M_BOOT = 0, M_WAIT_DEPLOY, M_DEPLOY, M_WAIT_RF, M_DETUMBLE, M_NOMINAL, M_SAFE } eor_mode_t;

/* ---- link layer: CCSDS space packet + AON authentication trailer
   TC:  [primary header 6][cmd 1][args n][seq 4, big endian][HMAC-SHA256(key, header..seq) first 16]
   TM:  [primary header 6][type 1][data n][CRC-16/CCITT 2]
   Commands are authenticated (HMAC, strictly increasing seq kept in FRAM); telemetry is open so any station can hear it. */
#define APID_TC          0x0A1
#define APID_TM_HK       0x0B1
#define APID_TM_SF       0x0B2
#define APID_TM_ACK      0x0B3
#define MAC_LEN          16
#define MAX_FRAME        255

enum { CMD_PING = 1, CMD_SET_MODE = 2, CMD_GET_HK = 3, CMD_SF_STORE = 4, CMD_SF_FETCH = 5, CMD_SF_DELETE = 6, CMD_SF_COUNT = 7,
       CMD_DEPLOY_ARM = 8, CMD_DEPLOY_FIRE = 9, CMD_SET_TIME = 10, CMD_TX_ENABLE = 11 };
enum { ACK_OK = 0, ERR_AUTH = 1, ERR_REPLAY = 2, ERR_FORMAT = 3, ERR_STATE = 4, ERR_FULL = 5, ERR_NOTFOUND = 6 };

/* ---- store-and-forward queue in NOR: fixed 256-byte slots, 4 KiB sectors, ring */
#define SF_SLOT          256u
#define SF_MSG_MAX       (SF_SLOT - 12u)
#define SF_BASE          0x00100000u
#define SF_SLOTS         2048u          /* 512 KiB of queue; the rest of the 128 MiB is for payload data */

typedef struct {
    eor_mode_t mode;
    uint32_t   boot_count, safe_count;
    uint32_t   tc_seq;                  /* last accepted command sequence */
    uint8_t    deployed[2], burn_tries[2];
    uint8_t    deploy_armed;
    uint8_t    tx_enabled;              /* ground can silence the transmitter (FCC stop-transmission requirement) */
    uint8_t    heater_on;
    uint32_t   last_beacon_s, last_burn_s;
    uint32_t   burn_until_ms; int8_t burning;
    uint32_t   sf_head, sf_tail, sf_count, sf_next_id;
    float      b_prev[3]; uint32_t b_prev_ms; uint8_t b_valid;
    uint32_t   rx_ok, rx_bad_auth, rx_replay, tx_frames;
    uint8_t    key[32];
} eor_t;

void   eor_init(eor_t *s, const uint8_t key[32]);
void   eor_tick(eor_t *s);                                        /* call every 100 ms */
int    eor_handle_tc(eor_t *s, const uint8_t *f, size_t n, uint8_t *resp, size_t *rn);
size_t eor_hk(const eor_t *s, uint8_t *out);                      /* beacon / HK frame */
void   bdot(const float b_nT[3], const float b_prev_nT[3], float dt_s, float m_out[3]);

/* helpers shared with tests and the ground tools */
uint16_t crc16_ccitt(const uint8_t *d, size_t n);
size_t   tc_build(const uint8_t key[32], uint32_t seq, uint8_t cmd, const uint8_t *args, size_t an, uint8_t *out);
int      sf_store(eor_t *s, const uint8_t *msg, size_t n, uint32_t *id);
int      sf_fetch(eor_t *s, uint32_t id, uint8_t *msg, size_t *n);
int      sf_delete_oldest(eor_t *s);
#endif
