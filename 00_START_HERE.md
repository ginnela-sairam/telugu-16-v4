# 🚀 START HERE — TELUGU T-16 V4.1

## What is this?

The **TELUGU T-16** is a 16-bit microprocessor chip designed from scratch. V4 is the definitive version that merges the best of all previous versions and is ready for real silicon fabrication via TinyTapeout.

## What makes T-16 V4 special?

1. **Sub-threshold ring oscillator** — an on-die 15-inverter ring that keeps oscillating even at 0.28V (way below the normal 1.8V). Its frequency is your temperature/voltage sensor.

2. **The P-bit (your idea!)** — a thermal-adaptive controller. When the chip is hot, the ring oscillator speeds up (Inverse Temperature Dependence). Software reads this and switches between ECO mode (sleep to save power) and TURBO mode (race to finish). Heat literally becomes your ally.

3. **Self-clock mode** — the CPU can run from its own ring oscillator (RO/32) with ZERO external clock. No crystal, no PLL — just physics.

4. **Clean single-cycle architecture** — 8 registers, 14 instructions, one instruction per clock. Proven by machine verification.

## Your first 3 commands (in Ubuntu terminal)

```bash
# Step 1: Set up the project in Ubuntu
# (works from the Windows Desktop path OR from wherever you unzipped it:
#  cd /path/to/T16_V4.1 && bash setup_ubuntu.sh)
bash /mnt/c/Users/shaik/Desktop/TELUGU-16/T16_V4.1/setup_ubuntu.sh

# Step 2: Go to the project
cd ~/t16/T16_V4.1

# Step 3: Run ALL tests (~1 minute — the self-clocked phase is the slow part)
bash run_sim.sh
```

**Expected result: `ALL 4 TESTS PASSED — T-16 V4.1 VERIFIED`**

## What's in this folder?

| Folder | What it contains |
|--------|-----------------|
| `rtl/` | All synthesizable Verilog (the actual chip design) |
| `tb/`  | 4 testbenches (verify the chip works correctly) |
| `sw/`  | Assembly programs (Fibonacci, ISA test, P-bit demo) |
| `tools/` | Assembler, ROM baker, PDF generator (+ pdfgen/ build sources) |
| `spice/` | Transistor-level experiments + real sky130 models + results |
| `openlane/` | Reference copies + config for the OpenLane flow |
| `docs/` | Master guide (MD + PDF), ISA card, command reference |
| `build/` | Created by scripts — compiled simulations, waveforms |
| `EDITS_AND_VERIFICATION.md` | What V4.1 changed and why — read it second |

## The 2-day plan

- **Day 1 (Monday)**: Run simulations, write programs, run SPICE experiments, Yosys synthesis
- **Day 2 (Tuesday)**: OpenLane GDS flow, view your chip layout, prepare TinyTapeout submission

## Key scripts

| Script | What it does | Command |
|--------|-------------|---------|
| `run_sim.sh` | Runs all 4 verification tests | `bash run_sim.sh` |
| `run_synthesis.sh` | Logic synthesis with Yosys | `bash run_synthesis.sh` |
| `run_openlane.sh` | OpenLane 1.0.2 GDS flow setup | `bash run_openlane.sh` |
| `setup_ubuntu.sh` | One-time Ubuntu setup | `bash setup_ubuntu.sh` |

## Need help?

Read `docs/COMMANDS.md` for every command you'll ever need.
Read `docs/ISA_CARD.md` for the instruction set quick reference.
