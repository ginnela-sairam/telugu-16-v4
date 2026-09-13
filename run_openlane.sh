#!/bin/bash
# ============================================================================
#  run_openlane.sh  —  Full RTL-to-GDS ASIC Flow (V4.1, OpenLane 1.0.2)
# ----------------------------------------------------------------------------
#  You have OpenLane v1.0.2 (Docker) — this script matches exactly how you
#  already used it (make mount -> ./flow.tcl -design <name>).
#
#  WHAT THIS SCRIPT DOES (on the Ubuntu/WSL side, outside Docker):
#    1. Finds your OpenLane checkout
#    2. Re-bakes the program into rtl/t16_rom.v (so the GDS contains it)
#    3. Copies the RTL into OpenLane's designs/telugu_t16_v4/src/
#    4. Writes a config.json that OpenLane 1.0.2 understands
#
#  THEN YOU RUN THE FLOW INSIDE THE CONTAINER (the script prints the exact
#  commands when it finishes):
#    make mount
#    ./flow.tcl -design telugu_t16_v4
#
#  The result: your chip's GDS (the actual silicon layout).
#
#  WHY THE TOP IS t16_top_silicon (not t16_soc):
#    t16_soc's default parameters are for SIMULATION (no ring, program from
#    a file). t16_top_silicon is the same proven SoC configured the way it
#    must be in silicon: real 15-inverter sky130 ring (USE_RO=1), SENSOR on
#    RO/256 (SENSOR_TAP=7), and the program BAKED into the ROM gates
#    (INIT_FILE=""). Send THAT to the factory.
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

DESIGN_NAME="telugu_t16_v4"

echo ""
echo "  ==================================================="
echo "   T-16 V4.1  —  OpenLane RTL-to-GDS Flow setup"
echo "   (for OpenLane 1.0.2 with Docker, your setup)"
echo "  ==================================================="
echo ""

# ---- 1. Find OpenLane -------------------------------------------------------
# Honors an exported OPENLANE_DIR first (see the error message below).
OPENLANE_DIR="${OPENLANE_DIR:-}"
for CAND in "$OPENLANE_DIR" "$HOME/OpenLane" "$HOME/openlane" \
            "$HOME/OpenLane2" "$HOME/openlane2" /openlane /openLane; do
    if [ -n "$CAND" ] && [ -f "$CAND/flow.tcl" ]; then
        OPENLANE_DIR="$CAND"
        break
    fi
done

if [ -z "$OPENLANE_DIR" ]; then
    echo "  Looking for OpenLane (searching for flow.tcl) ..."
    FOUND=$(find "$HOME" -maxdepth 3 -name "flow.tcl" -type f 2>/dev/null | head -1)
    if [ -n "$FOUND" ]; then
        OPENLANE_DIR=$(dirname "$FOUND")
    fi
fi

if [ -z "$OPENLANE_DIR" ]; then
    echo "  PROBLEM: could not find your OpenLane directory."
    echo ""
    echo "  You already have it working (your terminal history shows"
    echo "  'make mount' and './flow.tcl' inside the container)."
    echo ""
    echo "  FIX: either"
    echo "    export OPENLANE_DIR=/path/to/your/OpenLane   (then re-run)"
    echo "  or edit this script and set OPENLANE_DIR near the top."
    exit 1
fi
echo "  [1/4] Found OpenLane at: $OPENLANE_DIR"

# ---- 2. Bake the program into the ROM ---------------------------------------
echo "  [2/4] Baking the program into rtl/t16_rom.v ..."
if command -v python3 > /dev/null 2>&1; then
    python3 tools/bake_rom.py sw/program_fib.hex || {
        echo "  PROBLEM: baking failed."
        exit 1
    }
else
    echo "  WARNING: python3 not found - using the ROM as-is."
    echo "  (The Fibonacci program is already baked in by default.)"
fi

# ---- 3. Copy RTL into the design directory ----------------------------------
DESIGN_DIR="$OPENLANE_DIR/designs/$DESIGN_NAME"
mkdir -p "$DESIGN_DIR/src"

cp rtl/t16_rom.v            "$DESIGN_DIR/src/"
cp rtl/t16_ram.v            "$DESIGN_DIR/src/"
cp rtl/t16_gpio.v           "$DESIGN_DIR/src/"
cp rtl/t16_cpu.v            "$DESIGN_DIR/src/"
cp rtl/t16_ro.v             "$DESIGN_DIR/src/"
cp rtl/t16_soc.v            "$DESIGN_DIR/src/"
cp rtl/t16_top_silicon.v    "$DESIGN_DIR/src/"

# Keep a reference copy inside this package too
mkdir -p openlane
cp rtl/t16_rom.v rtl/t16_ram.v rtl/t16_gpio.v rtl/t16_cpu.v \
   rtl/t16_ro.v rtl/t16_soc.v rtl/t16_top_silicon.v openlane/ 2>/dev/null

echo "  [3/4] Copied 7 RTL files to $DESIGN_DIR/src/"

# ---- 4. Write the OpenLane 1.0.2 config.json --------------------------------
cat > "$DESIGN_DIR/config.json" << 'ENDCONFIG'
{
    "DESIGN_NAME": "t16_top_silicon",
    "VERILOG_FILES": ["dir::src/*.v"],
    "CLOCK_PORT": "clk",
    "CLOCK_PERIOD": 50.0,
    "FP_SIZING": "absolute",
    "DIE_AREA": "0 0 600 600",
    "CORE_AREA": "10 10 590 590",
    "PL_TARGET_DENSITY": 0.45,
    "SYNTH_MAX_FANOUT": 10,
    "RUN_LINTER": 0,
    "SYNTH_READ_BLACKBOX_LIB": 1
}
ENDCONFIG

cp "$DESIGN_DIR/config.json" openlane/config.json

echo "  [4/4] Wrote $DESIGN_DIR/config.json"
echo ""
echo "  WHAT THE CONFIG MEANS:"
echo "    DESIGN_NAME    t16_top_silicon  - the silicon top (real ring,"
echo "                                    baked program, RO/256 sensor)"
echo "    VERILOG_FILES  dir::src/*.v     - all 7 RTL files"
echo "    CLOCK_PORT     clk              - the external clock pin"
echo "    CLOCK_PERIOD   50 ns            - 20 MHz, relaxed on purpose:"
echo "                                    correctness first, speed later"
echo "    DIE_AREA       600x600 um       - plenty of room for the first run"
echo "    CORE_AREA      590x590 um       - cells live here (auto-margin is"
echo "                                    also fine; we set it explicitly)"
echo "    PL_TARGET_DENSITY 0.45          - 45% cell fill, comfortable"
echo "    SYNTH_READ_BLACKBOX_LIB 1       - THE IMPORTANT ONE (see below)"
echo ""
echo "  WHY SYNTH_READ_BLACKBOX_LIB = 1 (read this once):"
echo "    Your ring oscillator is built by DIRECTLY instantiating two real"
echo "    sky130 cells (sky130_fd_sc_hd__inv_2 and ...__and2_0) in rtl/t16_ro.v."
echo "    OpenLane 1.0.2 does NOT pre-load the cell library during synthesis"
echo "    by default - so Yosys would fail at the very first step with"
echo "      ERROR: Module 'sky130_fd_sc_hd__inv_2' ... is not part of the design."
echo "    Setting this flag makes OpenLane read the liberty as blackboxes first:"
echo "    the cells resolve, flatten keeps them as real instances, and your"
echo "    ring (the physics heart) reaches the GDS intact. This was verified"
echo "    by emulating OpenLane 1.0.2's exact Yosys pass order: without the"
echo "    flag the flow dies at hierarchy check; with it, all 15 inverters"
echo "    plus the AND gate survive into the final netlist."
echo ""
echo "  ==================================================="
echo "   Setup complete! Now run the flow INSIDE the container:"
echo "  ==================================================="
echo ""
echo "   1) Enter the OpenLane container (you did this before):"
echo ""
echo "        cd $OPENLANE_DIR"
echo "        make mount"
echo ""
echo "   2) Run the flow (15-45 minutes, lots of output):"
echo ""
echo "        ./flow.tcl -design $DESIGN_NAME"
echo ""
echo "   3) SUCCESS looks like (you have seen it before):"
echo ""
echo "        [SUCCESS]: Flow complete."
echo ""
echo "   4) Your chip's GDS is at:"
echo ""
echo "        $DESIGN_DIR/runs/RUN_*/results/final/gds/*.gds"
echo ""
echo "   5) Open it and LOOK AT YOUR CHIP:"
echo ""
echo "        klayout $DESIGN_DIR/runs/RUN_*/results/final/gds/*.gds"
echo ""
echo "      (In KLayout: the grey blobs are standard cells, the thin"
echo "       lines are metal wires. Somewhere in there: your CPU, your"
echo "       ROM with Fibonacci baked into gates, and 15 inverters in"
echo "       a ring - the physics heart.)"
echo ""
echo "  ==================================================="
echo ""
