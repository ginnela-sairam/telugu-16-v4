# openlane/ — what goes into the OpenLane flow (V4.1)

This folder holds the **copies** that `run_openlane.sh` places here for
reference. The live copies live inside your OpenLane checkout at
`designs/telugu_t16_v4/` — that is the directory the Docker flow reads.

## Files you will find here after running `bash run_openlane.sh`

| File | What it is |
|------|------------|
| `config.json` | The OpenLane 1.0.2 configuration for the flow |
| `t16_top_silicon.v` | The SILICON top module (USE_RO=1, baked program) |
| `t16_soc.v`, `t16_cpu.v`, `t16_rom.v`, `t16_ram.v`, `t16_gpio.v`, `t16_ro.v` | The design itself |

## The one config line you must never delete

```json
"SYNTH_READ_BLACKBOX_LIB": 1
```

Your ring oscillator instantiates two **real sky130 cells** directly
(`sky130_fd_sc_hd__inv_2`, `sky130_fd_sc_hd__and2_0` in `rtl/t16_ro.v`).
OpenLane 1.0.2 does not pre-load the cell library during synthesis by
default, so without this line Yosys dies at the very first check with:

```
ERROR: Module `\sky130_fd_sc_hd__inv_2' referenced in module
`$paramod\t16_ro\...' in cell `\g_ring.g_inv[0].u_inv'
is not part of the design.
```

With the flag set, OpenLane reads the liberty cells as blackboxes first.
The ring cells then survive `flatten` as real instances (verified by
running OpenLane 1.0.2's exact Yosys pass order: all 15 inverters plus
the AND gate reach the final netlist). **No flag = no ring = no
self-clocked chip.** If you rebuild a config by hand, keep this line.

The other silicon-critical keys: `DIE_AREA`/`CORE_AREA` (400x400 um die,
380x380 um core) and `FP_SIZING: "absolute"`.

## The one design decision to understand

OpenLane synthesizes **`t16_top_silicon`**, not `t16_soc`. Why?

`t16_soc`'s default parameters are tuned for simulation: the ring
oscillator is replaced by a pretend clock input (`USE_RO=0`) and the
program comes from a `.hex` file. If that went to silicon, the GDS would
contain **no ring oscillator** — the physics heart of the project would
be missing.

`t16_top_silicon` wraps the exact same verified SoC with the parameters
silicon needs:

- `USE_RO = 1` — the real 15-inverter ring, built from sky130 cells
- `SENSOR_TAP = 7` — the sensor counts RO/256 (safe at any VDD)
- `INIT_FILE = ""` — no file to find inside Docker; the program is
  baked into `t16_rom.v` by `tools/bake_rom.py`

## To change the program that goes into silicon

```bash
python3 tools/bake_rom.py sw/program_pbit.hex   # bake the P-bit demo
bash run_openlane.sh                             # re-copy + re-config
# then, inside the container:
#   ./flow.tcl -design telugu_t16_v4 -tag pbit   (-tag keeps runs separate)
```

## For the real TinyTapeout submission

Use `rtl/tt_um_telugu_t16.v` as the top instead — it maps the same
silicon configuration onto TinyTapeout's fixed pin budget. See the
master guide, Chapter 16, for the fork-template-push-submit recipe.
