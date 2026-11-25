# TELUGU-16 V4.1 — Tiny Tapeout project notes

## How it works

TELUGU-16 is a 16-bit, single-cycle RISC SoC. The Tiny Tapeout wrapper
`tt_um_telugu_t16` connects the processor to the GPIO, timer, sensor, and
probabilistic-bit peripherals. In self-clock mode, an on-chip ring oscillator
provides the processor clock. The wrapper exposes the GPIO and selected
processor/oscillator status signals on the Tiny Tapeout pins.

The project sources remain in the repository's `rtl/` directory. The
`info.yaml` source paths are relative to Tiny Tapeout's `src/` source root and
refer to those existing files, rather than a second copy that could become
out of sync.

## How to test

Run the repository's RTL simulations with `bash run_sim.sh` (Icarus Verilog is
required). The test suite exercises the ISA, SoC, P-bit, and silicon wrapper.

For pin-level operation, `ui[0]` is `CLKSEL`: set it to 0 to use `clk`, or to 1
to use the ring oscillator. Keep this selection static while the chip is
running. `rst_n` is active-low. `ui[1]` through `ui[7]` feed GPIO input bits 1
through 7; GPIO input bit 0 is the clock-select signal. `uo[7:0]` show GPIO
output bits 7:0. `uio[7:4]` show GPIO output bits 11:8, while `uio[3:0]` show
the ring-oscillator output, sleeping status, halted status, and P-bit status,
respectively. The wrapper drives all `uio` pins as outputs; `uio_in` is unused.

No external components are required for the digital interface. The ring
oscillator uses SkyWater 130nm standard cells, so the target shuttle's
hardening flow must support the project's PDK-specific oscillator cells.
