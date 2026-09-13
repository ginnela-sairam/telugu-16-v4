#!/bin/bash
# ============================================================================
#  run_synthesis.sh  —  Yosys Logic Synthesis (V4.1)
# ----------------------------------------------------------------------------
#  Synthesizes the T-16 design and reports:
#    - Cell count (how many gates)
#    - Area estimate
#    - Any warnings or errors
#
#  WHAT IS SYNTHESIZED: the SIMULATION configuration of t16_soc
#  (USE_RO=0, so the ring is a stand-in clock input). The ring oscillator
#  itself is made of sky130 transistors, not generic gates - it goes into
#  the GDS via the OpenLane flow (run_openlane.sh) with the SILICON top
#  (t16_top_silicon), where Yosys maps it to real sky130 cells.
#
#  Run:  bash run_synthesis.sh
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "  ==================================================="
echo "   T-16 V4.1  —  Yosys Logic Synthesis"
echo "  ==================================================="
echo ""

if ! command -v yosys > /dev/null 2>&1; then
    echo "  PROBLEM: 'yosys' was not found."
    echo "  FIX:     sudo apt install yosys"
    exit 1
fi
echo "  Using $(yosys -V 2>&1 | head -1)"
echo ""

mkdir -p build

yosys -p "
    # ---- read the design (simulation configuration) ----
    read_verilog rtl/t16_rom.v;
    read_verilog rtl/t16_ram.v;
    read_verilog rtl/t16_gpio.v;
    read_verilog rtl/t16_cpu.v;
    read_verilog rtl/t16_ro.v;
    read_verilog rtl/t16_soc.v;

    hierarchy -check -top t16_soc;

    proc;
    opt;
    fsm;
    opt;
    memory;
    opt;

    synth -top t16_soc;

    stat;

    write_verilog build/t16_soc_synth.v;
" 2>&1 | tee build/synthesis_log.txt

echo ""
echo "  ==================================================="
echo "   Synthesis complete. Highlights to look for in"
echo "   build/synthesis_log.txt:"
echo ""
echo "     - the 'stat' section near the end:"
echo "         Number of cells:  XXXX   <- your gate count"
echo "     - zero 'ERROR' lines"
echo ""
echo "   Synthesized netlist: build/t16_soc_synth.v"
echo "  ==================================================="
echo ""
