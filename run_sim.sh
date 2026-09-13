#!/bin/bash
# ============================================================================
#  run_sim.sh  —  THE ONE COMMAND THAT DOES EVERYTHING (V4.1)
# ----------------------------------------------------------------------------
#  Runs ALL FOUR test suites:
#    TEST 1: Fibonacci on GPIO (the original proof)
#    TEST 2: Every-instruction coverage (the ISA proof)
#    TEST 3: P-bit thermal-adaptive system (eco sleeps, turbo races)
#    TEST 4: the SILICON configuration (baked ROM + real sky130 ring +
#            a CPU that runs with NO external clock at all)
#  All four must print PASSED for the chip to be considered verified.
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "  ==================================================="
echo "   T-16 V4.1  —  Full Verification Suite"
echo "   (4 tests: Fibonacci + ISA + P-bit + Silicon config)"
echo "  ==================================================="
echo ""

# ---- tool check -----------------------------------------------------------
if ! command -v iverilog > /dev/null 2>&1; then
    echo "  PROBLEM: 'iverilog' (Icarus Verilog) was not found."
    echo "  FIX:     sudo apt install iverilog"
    exit 1
fi
echo "  Using Icarus Verilog: $(iverilog -V 2>/dev/null | head -1)"
echo ""

mkdir -p build

# ---- compile all four tests ------------------------------------------------
echo "  [1/8] Compiling TEST 1 (Fibonacci) ..."
iverilog -g2012 -Wall -o build/sim_fib \
    rtl/t16_rom.v rtl/t16_ram.v rtl/t16_gpio.v rtl/t16_cpu.v rtl/t16_ro.v rtl/t16_soc.v \
    tb/tb_t16_soc.v

echo "  [2/8] Compiling TEST 2 (instruction coverage) ..."
iverilog -g2012 -Wall -o build/sim_isa \
    rtl/t16_rom.v rtl/t16_ram.v rtl/t16_gpio.v rtl/t16_cpu.v rtl/t16_ro.v rtl/t16_soc.v \
    tb/tb_t16_isa.v

echo "  [3/8] Compiling TEST 3 (P-bit thermal system) ..."
iverilog -g2012 -Wall -DT16_SIM -o build/sim_pbit \
    rtl/t16_rom.v rtl/t16_ram.v rtl/t16_gpio.v rtl/t16_cpu.v rtl/t16_ro.v rtl/t16_soc.v \
    tb/sky130_shims.v tb/tb_t16_pbit.v

echo "  [4/8] Compiling TEST 4 (silicon configuration) ..."
iverilog -g2012 -Wall -DT16_SIM -o build/sim_silicon \
    rtl/t16_rom.v rtl/t16_ram.v rtl/t16_gpio.v rtl/t16_cpu.v rtl/t16_ro.v rtl/t16_soc.v \
    rtl/t16_top_silicon.v tb/sky130_shims.v tb/tb_t16_silicon.v

echo ""
echo "  [5/8] Running TEST 1 ..."
echo "  ---------------------------------------------------"
vvp build/sim_fib | tee build/log_fib.txt

echo ""
echo "  [6/8] Running TEST 2 ..."
echo "  ---------------------------------------------------"
vvp build/sim_isa | tee build/log_isa.txt

echo ""
echo "  [7/8] Running TEST 3 ..."
echo "  ---------------------------------------------------"
vvp build/sim_pbit | tee build/log_pbit.txt

echo ""
echo "  [8/8] Running TEST 4 (self-clocked phase runs the CPU at ring"
echo "        speed - about a minute) ..."
echo "  ---------------------------------------------------"
vvp build/sim_silicon | tee build/log_silicon.txt

# ---- final verdict -----------------------------------------------------------
echo ""
PASS1=$(grep -c "TEST 1 PASSED" build/log_fib.txt)
PASS2=$(grep -c "TEST 2 PASSED" build/log_isa.txt)
PASS3=$(grep -c "TEST 3 PASSED" build/log_pbit.txt)
PASS4=$(grep -c "TEST 4 PASSED" build/log_silicon.txt)

echo "  ==================================================="
if [ "$PASS1" -ge 1 ] && [ "$PASS2" -ge 1 ] && [ "$PASS3" -ge 1 ] && [ "$PASS4" -ge 1 ]; then
    echo "   *** ALL 4 TESTS PASSED — T-16 V4.1 VERIFIED ***"
    echo ""
    echo "   What you just proved:"
    echo "     1. the CPU computes correctly (Fibonacci)"
    echo "     2. every instruction works (full ISA coverage)"
    echo "     3. the P-bit system decides eco/turbo correctly,"
    echo "        sleeps in eco, races in turbo"
    echo "     4. the SILICON configuration boots: baked program,"
    echo "        real ring, self-clocked CPU with no external clock"
    echo ""
    echo "   Waveforms saved:"
    echo "     build/tb_t16_soc.vcd      (Fibonacci run)"
    echo "     build/tb_t16_isa.vcd      (instruction test)"
    echo "     build/tb_t16_pbit.vcd     (P-bit thermal demo)"
    echo "     build/tb_t16_silicon.vcd  (self-clocked silicon run)"
    echo ""
    echo "   To watch signals:"
    echo "     gtkwave build/tb_t16_soc.vcd"
else
    echo "   *** AT LEAST ONE TEST FAILED ***"
    echo "   Test 1 (Fibonacci):      $([ $PASS1 -ge 1 ] && echo PASS || echo FAIL)"
    echo "   Test 2 (ISA):            $([ $PASS2 -ge 1 ] && echo PASS || echo FAIL)"
    echo "   Test 3 (P-bit):          $([ $PASS3 -ge 1 ] && echo PASS || echo FAIL)"
    echo "   Test 4 (Silicon config): $([ $PASS4 -ge 1 ] && echo PASS || echo FAIL)"
    echo ""
    echo "   Read the [FAIL] lines above for details."
fi
echo "  ==================================================="
echo ""
