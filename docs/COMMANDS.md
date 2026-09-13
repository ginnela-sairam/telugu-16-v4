# T-16 V4.1 — Complete Command Reference

Every command you'll need, organized by task. All commands run in Ubuntu/WSL.

## 🔧 Initial Setup (run once)

```bash
# Copy project to Ubuntu and install tools
bash /mnt/c/Users/shaik/Desktop/TELUGU-16/T16_V4.1/setup_ubuntu.sh

# Navigate to the project
cd ~/t16/T16_V4.1
```

## ✅ Simulation & Verification

```bash
# Run ALL four tests at once (THE MAIN COMMAND)
bash run_sim.sh

# Run individual tests:
# Test 1: Fibonacci
iverilog -g2012 -Wall -o build/sim_fib rtl/*.v tb/tb_t16_soc.v && vvp build/sim_fib

# Test 2: ISA coverage
iverilog -g2012 -Wall -o build/sim_isa rtl/*.v tb/tb_t16_isa.v && vvp build/sim_isa

# Test 3: P-bit thermal system
iverilog -g2012 -Wall -DT16_SIM -o build/sim_pbit rtl/*.v tb/sky130_shims.v tb/tb_t16_pbit.v && vvp build/sim_pbit

# Test 4: the SILICON configuration (baked ROM + self-clocked CPU)
iverilog -g2012 -Wall -DT16_SIM -o build/sim_silicon rtl/*.v tb/sky130_shims.v tb/tb_t16_silicon.v && vvp build/sim_silicon
```

## 📊 View Waveforms

```bash
# After running a test, view the signals graphically
gtkwave build/tb_t16_soc.vcd    # Fibonacci waveform
gtkwave build/tb_t16_isa.vcd    # ISA test waveform
gtkwave build/tb_t16_pbit.vcd   # P-bit demo waveform
```

## 🔨 Write Your Own Program

```bash
# 1. Write assembly in a .asm file (see sw/program_fib.asm for example)
nano sw/my_program.asm

# 2. Assemble it
python3 tools/t16asm.py sw/my_program.asm sw/my_program.hex

# 3. Edit a testbench to use your program:
#    Change INIT_FILE parameter to "sw/my_program.hex"
#    in tb/tb_t16_soc.v

# 4. Simulate
iverilog -g2012 -Wall -o build/sim_mine rtl/*.v tb/tb_t16_soc.v && vvp build/sim_mine
```

## ⚙️ Logic Synthesis (Yosys)

```bash
# Synthesize the design and get cell count
bash run_synthesis.sh

# View the synthesis report
cat build/synthesis_log.txt

# Look for lines like:
#   Number of cells:  XXXX
#   Estimated area:   XXXX
```

## 🏭 OpenLane GDS Flow (Silicon Layout)

```bash
# Set up the design (copies RTL + config into OpenLane's designs folder)
bash run_openlane.sh

# Then enter the container and run the flow:
cd ~/OpenLane && make mount
./flow.tcl -design telugu_t16_v4

# View the result:
klayout ~/OpenLane/designs/telugu_t16_v4/runs/RUN_*/results/final/gds/*.gds
```

## 🔬 SPICE Physics Experiments

```bash
# Run all 3 physics experiments (30-60 min, real sky130 models)
cd spice
bash run_experiments.sh
# or one at a time: python3 run_experiments.py --only 1

# View results
cat results/ro_vdd_sweep.csv      # the heart curve
cat results/ro_temp_scissors.csv  # the ITD scissors
cat results/fbb_vth_shift.csv     # the body-bias story

# Interactive single-point demo (opens a plot):
ngspice ro_vdd_sweep.spice
```

## 📝 Assembly Language Cheat Sheet

```asm
; Load a constant into a register
LDI  R1, 42         ; R1 = 42

; Arithmetic
ADD  R3, R1, R2     ; R3 = R1 + R2
SUB  R3, R1, R2     ; R3 = R1 - R2

; Logic
AND  R3, R1, R2     ; R3 = R1 & R2
OR   R3, R1, R2     ; R3 = R1 | R2
XOR  R3, R1, R2     ; R3 = R1 ^ R2

; Shifts
SLL  R3, R1, R2     ; R3 = R1 << R2 (func=0)
SRL  R3, R1, R2     ; R3 = R1 >> R2 (func=1)
SRA  R3, R1, R2     ; R3 = R1 >>> R2 (func=2, arithmetic)

; Memory (accessing peripherals!)
LDM  R1, R4, R0     ; R1 = MEM[R4 + R0] (read TIMER, SENSOR, etc.)
STM  R1, [R4+R0]    ; MEM[R4 + R0] = R1 (write GPIO, P-bit, etc.)

; Branching
BEQZ R1, -5         ; if R1==0, jump back 5 instructions
BNEZ R1, 3          ; if R1!=0, jump forward 3 instructions
JAL  R7, target     ; call subroutine (return addr in R7)
JR   R7             ; return from subroutine

; Stop
HALT                ; CPU stops forever
```

## 🗺️ Address Map for Memory-Mapped I/O

```asm
; To read TIMER:
LDI  R4, 0x82       ; address of TIMER
LDI  R0, 0          ; zero offset
LDM  R1, R4, R0     ; R1 = current timer value

; To read SENSOR (ring oscillator speed):
LDI  R4, 0x83
LDM  R1, R4, R0     ; R1 = current sensor count

; To read/write P-bit:
LDI  R4, 0x84
LDM  R1, R4, R0     ; R1 = current P-bit (bit 0)
LDI  R1, 1          ; turbo mode
STM  R1, [R4+R0]    ; set P = 1

; To write GPIO output:
LDI  R4, 0x80
LDI  R1, 0xFF
STM  R1, [R4+R0]    ; GPIO pins = 0x00FF
```
