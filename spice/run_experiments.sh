#!/bin/bash
# ============================================================================
#  run_experiments.sh — Run all SPICE physics experiments (V4.1)
# ----------------------------------------------------------------------------
#  These are the three silicon-physics experiments that prove the T-16's
#  key claims, using the REAL SkyWater sky130 models bundled in
#  sky130_models/ (no PDK installation needed):
#
#    EXP1  ro_vdd_sweep.csv   - ring frequency vs VDD, 0.10 V to 1.80 V
#                               (the "heart curve" of the project)
#    EXP2  ro_temp_scissors.csv - frequency vs temperature at 0.30 V AND
#                               1.80 V (inverse temperature dependence -
#                               the physics the P-bit rides on)
#    EXP3  fbb_vth_shift.csv  - effective Vth vs forward body bias
#                               (the honest circuit-level Vth story)
#
#  Takes 30-60 minutes total (sub-threshold points simulate slowly -
#  that slowness IS the physics). Grab a tea. Or run one at a time:
#      python3 run_experiments.py --only 1
#      python3 run_experiments.py --only 2
#      python3 run_experiments.py --only 3
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "  ==================================================="
echo "   T-16 V4.1 — SPICE Physics Experiments"
echo "   (real sky130 tt models, bundled - no PDK needed)"
echo "  ==================================================="
echo ""

if ! command -v ngspice > /dev/null 2>&1; then
    echo "  PROBLEM: 'ngspice' not found."
    echo "  FIX:     sudo apt install ngspice"
    exit 1
fi
if ! command -v python3 > /dev/null 2>&1; then
    echo "  PROBLEM: 'python3' not found."
    echo "  FIX:     sudo apt install python3"
    exit 1
fi
if [ ! -f sky130_models/models/corners/tt_mini.spice ]; then
    echo "  PROBLEM: bundled sky130 models not found."
    echo "  (expected spice/sky130_models/models/corners/tt_mini.spice)"
    exit 1
fi

echo "  Running the three experiments (30-60 minutes total)..."
echo "  Each voltage point is simulated with real transistor physics."
echo ""
python3 run_experiments.py "$@"

echo ""
echo "  ==================================================="
echo "   Experiments complete."
echo "   Results in spice/results/:"
echo "     ro_vdd_sweep.csv     (the heart curve)"
echo "     ro_temp_scissors.csv (the ITD scissors)"
echo "     fbb_vth_shift.csv    (the body-bias story)"
echo ""
echo "   One-point interactive demo (opens a plot):"
echo "     ngspice ro_vdd_sweep.spice"
echo "  ==================================================="
echo ""
