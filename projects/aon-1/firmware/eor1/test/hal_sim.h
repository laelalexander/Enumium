#ifndef HAL_SIM_H
#define HAL_SIM_H
#include "../src/eor.h"
typedef struct {
    uint32_t ms, acc, rtc_s, wdt_kicks, erases;
    hal_power_t p; int load[LOAD_N]; int burn[2]; uint32_t burn_ms[2], burn_count[2]; int released[2], jam[2]; int pa;
    uint32_t first_burn_s, first_tx_s, tx_count, tx_violation;
    float m[3], rate, angle;
    uint8_t rx[256]; size_t rx_len; uint8_t tx[300]; size_t tx_len;
} sim_t;
extern sim_t SIM;
void sim_reset(int keep_nv);
void sim_advance_ms(uint32_t ms);
#endif
