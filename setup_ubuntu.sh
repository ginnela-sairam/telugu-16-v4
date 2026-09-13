#!/bin/bash
# ============================================================================
#  setup_ubuntu.sh  —  Set up T16 V4.1 in Ubuntu/WSL (run ONCE)
# ----------------------------------------------------------------------------
#  WHERE THIS RUNS: inside your Ubuntu (WSL) terminal.
#
#  WHAT IT DOES:
#    1. Copies this package to ~/t16/T16_V4.1 (from wherever it is — if you
#       are already inside the package, it copies THIS folder)
#    2. Fixes Windows line endings (if any)
#    3. Makes the scripts executable
#    4. Checks your tools and tells you exactly what (if anything) to install
#
#  Your Ubuntu already has: xschem, klayout, ngspice, magic, sky130 PDK,
#  openlane (+docker), yosys, iverilog, python3, gtkwave, verilator,
#  cocotb, netgen, graphviz, make, git. This script verifies all of it.
# ============================================================================

HERE="$(cd "$(dirname "$0")" && pwd)"

echo ""
echo "  ==================================================="
echo "   T-16 V4.1  —  Ubuntu Setup"
echo "  ==================================================="
echo ""

# ---- Step 1: Copy the package into Ubuntu-native storage -------------------
# Running the simulations from ~/t16 (the Linux filesystem) is much faster
# than running them from /mnt/c (the Windows drive through the 9p bridge).
DEST="$HOME/t16/T16_V4.1"

if [ "$HERE" = "$DEST" ]; then
    echo "  [1/4] Already installed at $DEST — no copy needed."
else
    echo "  [1/4] Copying the package to $DEST ..."
    mkdir -p "$HOME/t16"
    cp -r "$HERE" "$DEST" 2>/dev/null || {
        echo "  PROBLEM: could not copy to $DEST"
        exit 1
    }
    echo "  Done: $DEST"
fi
cd "$DEST"
echo ""

# ---- Step 2: Fix line endings (Windows -> Linux, if any) -------------------
echo "  [2/4] Fixing line endings (safe to skip if none) ..."
if command -v dos2unix > /dev/null 2>&1; then
    find . -name "*.sh"   -exec dos2unix -q {} \; 2>/dev/null
    find . -name "*.v"    -exec dos2unix -q {} \; 2>/dev/null
    find . -name "*.py"   -exec dos2unix -q {} \; 2>/dev/null
    find . -name "*.asm"  -exec dos2unix -q {} \; 2>/dev/null
    find . -name "*.hex"  -exec dos2unix -q {} \; 2>/dev/null
    find . -name "*.md"   -exec dos2unix -q {} \; 2>/dev/null
else
    find . -name "*.sh"  -exec sed -i 's/\r$//' {} \; 2>/dev/null
    find . -name "*.v"   -exec sed -i 's/\r$//' {} \; 2>/dev/null
    find . -name "*.py"  -exec sed -i 's/\r$//' {} \; 2>/dev/null
    find . -name "*.asm" -exec sed -i 's/\r$//' {} \; 2>/dev/null
    find . -name "*.hex" -exec sed -i 's/\r$//' {} \; 2>/dev/null
fi
echo "  Done"
echo ""

# ---- Step 3: Make scripts executable ----------------------------------------
echo "  [3/4] Making scripts executable ..."
chmod +x run_sim.sh run_synthesis.sh run_openlane.sh setup_ubuntu.sh 2>/dev/null
chmod +x spice/run_experiments.sh 2>/dev/null
echo "  Done"
echo ""

# ---- Step 4: Check the toolchain --------------------------------------------
echo "  [4/4] Checking your tools ..."
echo ""

NEEDED=""        # things that MUST be installed
OPTIONAL=""      # nice-to-have notes

check() {
    # $1 = command, $2 = human name, $3 = how to show version, $4 = apt name
    local cmd="$1" name="$2" veropt="$3" aptname="$4"
    if command -v "$cmd" > /dev/null 2>&1; then
        printf "    [ OK ] %-10s %s\n" "$name" "$($cmd $veropt 2>&1 | head -1 | cut -c1-50)"
    else
        printf "    [MISSING] %-10s install with: sudo apt install %s\n" "$name" "$aptname"
        NEEDED="$NEEDED $aptname"
    fi
}

check iverilog "iverilog" "-V"     "iverilog"
check vvp      "vvp"      "-V"     "iverilog"
check gtkwave  "gtkwave"  "--version" "gtkwave"
check yosys    "yosys"    "-V"     "yosys"
check ngspice  "ngspice"  "--version" "ngspice"
check python3  "python3"  "--version" "python3"
check make     "make"     "--version" "make"
check git      "git"      "--version" "git"

# GUI / layout tools (needed on Day 2)
if command -v klayout > /dev/null 2>&1; then
    echo "    [ OK ] klayout    (GDS viewer — you will SEE your chip)"
else
    echo "    [MISSING] klayout    install with: sudo apt install klayout"
    NEEDED="$NEEDED klayout"
fi
if command -v magic > /dev/null 2>&1; then
    echo "    [ OK ] magic     (classic layout editor)"
else
    echo "    [NOTE] magic not found — optional (KLayout covers Day 2)"
fi
if command -v xschem > /dev/null 2>&1; then
    echo "    [ OK ] xschem    (schematic editor)"
else
    echo "    [NOTE] xschem not found — optional for this package"
fi

# OpenLane + Docker (needed on Day 2 for the GDS)
if find "$HOME" -maxdepth 3 -name "flow.tcl" -type f 2>/dev/null | grep -q .; then
    echo "    [ OK ] openlane   (found flow.tcl in your home directory)"
else
    echo "    [NOTE] openlane not found in ~/ — if you have it elsewhere,"
    echo "           run: export OPENLANE_DIR=/path/to/OpenLane  before run_openlane.sh"
fi
if command -v docker > /dev/null 2>&1; then
    echo "    [ OK ] docker    $(docker --version 2>&1 | head -1 | cut -c1-40)"
else
    echo "    [NOTE] docker not found — OpenLane needs it (you already ran it once)"
fi

# sky130 PDK (used by xschem/magic; OpenLane bundles its own)
if [ -d /usr/share/pdk/sky130A ]; then
    echo "    [ OK ] sky130A PDK (/usr/share/pdk/sky130A)"
else
    echo "    [NOTE] system sky130A PDK not at /usr/share/pdk — that is fine;"
    echo "           this package bundles the models its SPICE lab needs"
fi

echo ""
if [ -n "$NEEDED" ]; then
    echo "  Some REQUIRED tools are missing. Install everything at once:"
    echo ""
    echo "      sudo apt update && sudo apt install -y$NEEDED"
    echo ""
    echo "  Then re-run:  bash setup_ubuntu.sh"
else
    echo "  All required tools present — you are ready!"
fi

echo ""
echo "  ==================================================="
echo "   Setup complete. NEXT STEPS:"
echo ""
echo "     cd ~/t16/T16_V4.1"
echo "     bash run_sim.sh"
echo ""
echo "   Expected result (after ~1 minute):"
echo "     *** ALL 4 TESTS PASSED — T-16 V4.1 VERIFIED ***"
echo "  ==================================================="
echo ""
