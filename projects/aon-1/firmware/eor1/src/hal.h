/* EOR-1 hardware abstraction. The flight port (port/stm32h7, to be written with the E03 board) and the host simulator (test/hal_sim.c) both implement this. */
#ifndef EOR_HAL_H
#define EOR_HAL_H
#include <stdint.h>
#include <stddef.h>

typedef struct { float vbatt, ibatt, tbatt_c, tobc_c; float isolar[4]; } hal_power_t;   /* V, A, °C; solar panel currents +X,-X,+Y,-Y */

uint32_t hal_ms(void);                                  /* monotonic ms since boot */
uint32_t hal_rtc_s(void);                               /* seconds since separation, kept in FRAM across resets */
void     hal_rtc_set(uint32_t s);
void     hal_wdt_kick(void);                            /* external TPS3813 window watchdog on E03 */

/* persistent store (FRAM on E03, 256 kbit) */
int      hal_fram_read(uint32_t addr, void *d, size_t n);
int      hal_fram_write(uint32_t addr, const void *d, size_t n);

/* store-and-forward flash (MT25QL01G NOR on E03): sector erase 4 KiB */
int      hal_nor_read(uint32_t addr, void *d, size_t n);
int      hal_nor_write(uint32_t addr, const void *d, size_t n);
int      hal_nor_erase4k(uint32_t addr);

/* EPS load switches (E01) and burn wires (E05) */
enum { LOAD_COM = 0, LOAD_ADCS, LOAD_PAYLOAD, LOAD_HEATER, LOAD_BURN, LOAD_N };
void     hal_load(int load, int on);
void     hal_burn(int element, int on);                 /* element 0/1, each through its own MOSFET, fused by the EPS burn rail */
int      hal_antenna_deployed(int element);             /* element switch on E05: 1 = released */
void     hal_pa_enable(int on);                         /* COM PA gate; also held off by the E04 45-min hardware timer */

void     hal_power(hal_power_t *p);
void     hal_mag(float b_nT[3]);                        /* RM3100 on E03, body frame */
void     hal_torquer(const float m_Am2[3]);             /* PWM to the X/Y panel coils and the Z coil on E07 */

int      hal_radio_rx(uint8_t *buf, size_t max);        /* returns frame length or 0 */
int      hal_radio_tx(const uint8_t *buf, size_t n);
#endif
