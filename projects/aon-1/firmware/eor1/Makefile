# Host build and tests for EOR-1 (gcc or clang). The flight port (port/stm32h7, arm-none-eabi-gcc) is written with the E03 board; it is not in this package yet.
CFLAGS ?= -std=c11 -O2 -Wall -Wextra -Wno-unused-parameter -Werror
SRC = src/eor.c src/sha256.c
test: build/test_eor
	./build/test_eor
build/test_eor: $(SRC) test/test_eor.c test/hal_sim.c src/*.h test/*.h
	mkdir -p build && $(CC) $(CFLAGS) -Isrc -o $@ $(SRC) test/test_eor.c test/hal_sim.c -lm
clean:
	rm -rf build
.PHONY: test clean
