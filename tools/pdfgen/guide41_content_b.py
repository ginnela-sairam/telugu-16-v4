#!/usr/bin/env python3
"""T-16 V4.1 Master Guide content - chapters 10-19 + appendix."""
import os

from guide41_lib import (S, Spacer, body, bullets, callout, code_block,
                          data_table, figure, h1_block, h2_block, h3_block,
                          stat_row)

PKG = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ASSETS = os.path.join(PKG, "docs")

PBIT_PROGRAM = """; the decision core of program_pbit.asm (V4.1)
        LDI   R3, 3          ; threshold: "hot" if sensor >= 3
        SUB   R5, R2, R3     ; R5 = SENSOR - 3
        LDI   R4, 15         ; shift amount
        SRA   R4, R5, R4     ; 0xFFFF if negative (cool), 0 if not
        BNEZ  R4, eco        ; cool chip -> eco mode

turbo:  LDI   R1, 1         ; P-bit = 1
        ...                 ; marker 0x700B, no sleep, races on
eco:    LDI   R1, 0         ; P-bit = 0
        ...                 ; marker 0xEC00
show:   STM   R5, [GPIO]    ; show the marker
        STM   R7, [WAIT]    ; ask to sleep (hardware decides!)
        ...
        ADD   R5, R5, R7    ; +1 receipt - only if the CPU wakes up"""

SCISSORS_TABLE = [
    ["0.30 V @ 27 C", "6,739 Hz", "the sub-threshold heartbeat"],
    ["0.30 V @ 85 C", "82,214 Hz", "hot and sub-threshold: 12.2x FASTER"],
    ["1.80 V @ 27 C", "1.333 GHz", "normal operation"],
    ["1.80 V @ 85 C", "1.317 GHz", "hot and super-threshold: slightly slower"],
]

VTH_TABLE = [
    ["0.00", "0.693 V", "no body bias - the baseline"],
    ["+0.15", "0.661 V", "small discount"],
    ["+0.30", "0.623 V", "meaningful discount"],
    ["+0.45", "0.578 V", "deep discount"],
    ["+0.60", "0.534 V", "159 mV total - the honest ceiling of this lever"],
]


def ch10(story):
    story += h1_block(10, "Reading Waveforms", body(
        "A waveform is the heartbeat monitor of your design: time runs "
        "left to right, every signal is a lane, and you watch the CPU "
        "think. GTKWave opens any .vcd the testbenches saved, and the "
        "signals worth watching first are always the same handful. Start "
        "with the Fibonacci run - it is short, deterministic, and tells "
        "the whole story of a working machine."))
    story += code_block(
        "gtkwave build/tb_t16_soc.vcd",
        label="Open the Fibonacci waveform")
    story += data_table(
        ["Signal", "What to watch for"],
        [
            ["dut.clk", "the heartbeat - clean square wave"],
            ["dut.u_cpu.pc_r", "the program counter stepping 0,1,2...13"],
            ["dut.u_cpu.instr", "the fetched instruction words"],
            ["dut.bus_addr / bus_wdata", "address 0x0080 carrying each Fibonacci value"],
            ["dut.gpio_out", "1, 1, 2, 3, 5, 8, 13, 21, 34, 55 appearing on the pins"],
            ["dut.halted", "goes high at the end - program complete"],
        ],
        [0.34, 0.66],
        mono_cols=(0,),
        caption_text="Table 10.1 - The six signals that tell the whole story.")
    story += h2_block("The self-clocked waveform - seeing the physics",
                      body(
        "Open build/tb_t16_silicon.vcd and look at Phase B. The external "
        "clk lane goes quiet - it is only a time reference now - while "
        "dut.u_soc.ro_out_pin beats with the ring's own rhythm and the "
        "CPU's clock lanes tick at exactly RO/32 of that rhythm. The PC "
        "still steps through the same thirteen instructions, just slower, "
        "because the chip is now driving itself. This one screen is the "
        "record experiment made visible: a processor computing from its "
        "own physics, with no external clock at all."))
    story += bullets([
        "Left panel: navigate the design tree to <b>tb_t16_soc</b> / <b>dut</b>",
        "Middle panel: select signals, click <b>Append</b>",
        "Zoom: <b>+</b>/<b>-</b> keys; fit a range by dragging and pressing <b>f</b>",
        "Search: right-click a lane and choose a value pattern to jump to",
    ])


def ch11(story):
    story += h1_block(11, "The P-Bit - Your Thermal Innovation", body(
        "The P-bit is the idea that makes this chip yours: the silicon "
        "senses its own temperature through physics, software reads the "
        "sensor, and the machine changes its own behavior. At low voltage "
        "the ring oscillator speeds up when the die gets hotter - inverse "
        "temperature dependence, the exact opposite of normal chips. "
        "In that regime, heat is an ally: a hot sub-threshold chip is a "
        "fast one. The P-bit encodes the strategy: when the sensor says "
        "the chip is cool, save power by sleeping; when it says hot, "
        "race."))
    story += h2_block("How one register changes the machine's character",
                      body(
        "The mechanism is deliberately tiny. Register 0x0084 holds one "
        "bit, P. The WAIT register at 0x0085 is a request: 'may I sleep?'. "
        "The hardware answers according to P. With P = 0 the request is "
        "granted - the CPU clock freezes until TIMER bit 15 rises, the "
        "heartbeat that arrives every 32,768 cycles. With P = 1 the "
        "request is ignored entirely and the CPU races on. There is no "
        "operating system, no interrupt handler, no magic - one AND gate "
        "of policy around a sleep request."))
    story += code_block(PBIT_PROGRAM,
                        label="The decision core (from sw/program_pbit.asm)")
    story += h2_block("The proof - TEST 3's two phases", body(
        "The testbench runs the same program twice and only changes the "
        "ring's speed - the temperature proxy. A slow ring must produce "
        "eco behavior; a fast ring must produce turbo. The V4.1 upgrade "
        "made this test strict: it now checks exact GPIO receipts, the "
        "P-bit readback in RAM, and - the part the old version never "
        "checked - that the CPU really slept and really woke."))
    story += data_table(
        ["Phase", "Ring", "Sensor reads", "Program decides", "GPIO receipt"],
        [
            ["1 - cool", "slow (16 ns period)", "below 3", "eco: P=0, sleep, wake",
             "0xEC01"],
            ["2 - hot", "fast (5 ns period)", "3 or more", "turbo: P=1, no sleep",
             "0x700C"],
        ],
        [0.14, 0.22, 0.18, 0.28, 0.18],
        center_cols=(4,),
        caption_text="Table 11.1 - The two-phase proof. Same ROM, same "
                     "CPU; only physics differs.")
    story += stat_row([
        ("32,768", "cycles per heartbeat (TIMER bit 15)"),
        ("32777", "cycles the eco phase actually took"),
        ("0xEC01", "eco receipt: slept AND woke"),
        ("0x700C", "turbo receipt: raced straight through"),
    ])
    story += callout(
        "The +1 in the receipt is the wake-up proof. The final GPIO write "
        "happens only after the sleep (or its turbo bypass), so a plain "
        "0xEC00 would mean the CPU never woke. The testbench demands the "
        "incremented values - it cannot be fooled by a decision that was "
        "merely computed but never lived.",
        title="Why the receipts end in 01 and 0C")


def ch12(story):
    story += h1_block(12, "The Ring Oscillator - Physics Heart", body(
        "Fifteen inverters in a loop, an odd number, so the signal can "
        "never settle: it chases itself around the ring forever. That is "
        "the whole oscillator. Its speed is not set by a crystal or a "
        "config register - it is set by how fast each inverter can pull "
        "its output, which is set by supply voltage and temperature. "
        "This is why the ring is a sensor as well as a clock: its "
        "frequency IS the chip's physical condition, readable by counting "
        "pulses."))
    story += figure(os.path.join(ASSETS, "chart_heart_curve.png"),
                    "Figure 12.1 - The heart curve, measured with real "
                    "sky130 tt SPICE models at 27 C. The ring is alive "
                    "from 0.28 V (4.4 kHz) to 1.8 V (1.33 GHz) - a span "
                    "of six orders of magnitude.",
                    max_h=280)
    story += h2_block("The honest physics of the low end", body(
        "The ambition of this project was 0.14-0.15 V operation. The "
        "honest measurement says: with these devices at this corner, the "
        "ring stops oscillating measurably below 0.28 V. Above it, "
        "frequency climbs exponentially - the classic sub-threshold "
        "signature - from 4.4 kHz at 0.28 V through 67 kHz at 0.3 V to "
        "444 kHz at half a volt. An exponential means every millivolt "
        "buys a lot of speed, but also that 'a bit too low' collapses "
        "into 'stopped'. That honesty is a feature of this package: the "
        "record story is 'a verified self-clocked chip at the edge of "
        "its physics', not a claim nobody measured."))
    story += h2_block("Why heat helps below threshold - the scissors",
                      body(
        "Above threshold, hotter transistors are slower - carrier "
        "mobility drops. Below threshold, hotter transistors are "
        "dramatically faster - thermal energy pushes more carriers over "
        "the barrier, and the sub-threshold current is exponential in "
        "temperature. The two regimes cross like scissor blades, and the "
        "measurement below is the P-bit's entire reason to exist: at "
        "0.30 V, an 85 C die beats 12.2 times faster than a 27 C one. "
        "The chip's sensor counts those beats; the P-bit turns them into "
        "a decision."))
    story += figure(os.path.join(ASSETS, "chart_temp_scissors.png"),
                    "Figure 12.2 - The temperature scissors, measured: "
                    "sub-threshold speed rises with heat while "
                    "super-threshold speed falls.",
                    max_h=280)
    story += callout(
        "The ring's cells are real sky130 standard cells "
        "(sky130_fd_sc_hd__inv_2), marked dont_touch so no tool ever "
        "optimizes the physics away. Getting them through synthesis "
        "intact is a story in itself - Chapter 14 tells it, because it "
        "is the one place the flow could have silently killed your chip's "
        "heart.",
        title="15 inverters that must survive the tools")


def ch13(story):
    story += h1_block(13, "Yosys Synthesis - Code to Gates", body(
        "Synthesis is the translation from behavior to structure: "
        "'R3 = R1 + R2' becomes a specific network of AND, OR and XOR "
        "gates wired together. Yosys reads the RTL, optimizes it, "
        "resolves memories, and writes a gate-level netlist. The package "
        "script runs the whole thing in one command and saves the log - "
        "your job is to read two things in it: zero errors, and the "
        "cell count."))
    story += code_block(
        "cd ~/t16/T16_V4\nbash run_synthesis.sh\n# output: build/synthesis_log.txt + build/t16_soc_synth.v",
        label="Monday 1:00 PM - the synthesis run")
    story += h2_block("What the log tells you", body(
        "Near the end of build/synthesis_log.txt you will find the stat "
        "block: the number of wires and cells for the top module. That "
        "number is your first real measure of the chip's size. In the "
        "verification runs for this edition the simulation configuration "
        "synthesized cleanly with zero errors, the baked ROM compressing "
        "into constant logic and the CPU plus peripherals flattening into "
        "on the order of a few thousand generic gates - the exact count "
        "varies with your Yosys version, so treat it as a sanity check "
        "and a number to write down, not a fixed constant to match "
        "digit-for-digit."))
    story += data_table(
        ["What to look for", "Where", "Healthy looks like"],
        [
            ["Errors", "whole log", "zero ERROR lines"],
            ["Hierarchy check", "early in log", "module t16_soc resolves, no missing modules"],
            ["Cell count", "stat block near end", "low thousands (sim top, generic gates)"],
            ["Netlist file", "build/t16_soc_synth.v", "written, ~500 KB of gates"],
        ],
        [0.28, 0.30, 0.42],
        caption_text="Table 13.1 - The four things to verify in the "
                     "synthesis log.")
    story += h2_block("Why the script synthesizes the sim configuration",
                      body(
        "run_synthesis.sh targets t16_soc with USE_RO=0 - the simulation "
        "configuration - on purpose. It is a fast, self-contained check "
        "that your Verilog maps to generic gates with zero errors. The "
        "ring oscillator is deliberately NOT part of this run: it is made "
        "of real sky130 cells, not generic logic, and it belongs to the "
        "OpenLane flow where the sky130 library is present. The silicon "
        "top (t16_top_silicon, USE_RO=1) was separately verified through "
        "an exact emulation of OpenLane's own synthesis pass sequence - "
        "that story, and the config line it depends on, is Chapter 14."))
    story += callout(
        "The -DUSE_RO=0 flag you may remember from V4.0 did nothing: "
        "USE_RO is a Verilog parameter, not a preprocessor define. V4.1 "
        "fixed the actual default so that plain Yosys runs work out of "
        "the box, and the silicon tops pass 1 explicitly.",
        title="A small V4.1 fix worth remembering")


def ch14(story):
    story += h1_block(14, "OpenLane GDS Flow - Gates to Silicon", body(
        "OpenLane is the conductor that turns the netlist into geometry: "
        "floorplanning draws the die, placement arranges every cell, CTS "
        "builds the clock tree, routing wires it all in metal, and "
        "signoff checks DRC, LVS and timing. Roughly forty-two steps "
        "later, a GDSII file exists that describes your chip as literal "
        "polygons. You have already run OpenLane once on the demo design; "
        "this chapter is the same muscle, pointed at your own chip."))
    story += code_block(
        "# STEP 1 - on the Ubuntu side (outside Docker):\n"
        "cd ~/t16/T16_V4\n"
        "bash run_openlane.sh\n"
        "# (re-bakes the ROM, copies 7 RTL files, writes config.json)\n"
        "\n"
        "# STEP 2 - enter the container (you know this one):\n"
        "cd ~/OpenLane            # wherever your checkout is\n"
        "make mount\n"
        "\n"
        "# STEP 3 - run the flow (15-45 minutes):\n"
        "./flow.tcl -design telugu_t16_v4",
        label="Monday evening - the three steps to your GDS")
    story += h2_block("Why the top is t16_top_silicon", body(
        "The config synthesizes t16_top_silicon, not t16_soc. The reason: "
        "t16_soc's default parameters are for simulation - the ring is a "
        "pretend clock input and the program comes from a .hex file that "
        "Docker cannot find. t16_top_silicon is the same verified SoC "
        "configured the way silicon needs it: USE_RO=1 builds the real "
        "15-inverter ring, SENSOR_TAP=7 puts the sensor on RO/256 so it "
        "counts safely at any VDD, and INIT_FILE is empty so the program "
        "comes from the baked ROM words. TEST 4 in run_sim.sh proves this "
        "exact configuration boots and computes - including with no "
        "external clock."))
    story += h2_block("The config line that keeps your ring alive",
                      body(
        "One line in the generated config.json is the difference between "
        "a chip with a physics heart and a flow that dies in its first "
        "minute: SYNTH_READ_BLACKBOX_LIB set to 1. Your ring instantiates "
        "two real sky130 cells directly, and OpenLane 1.0.2 does not "
        "pre-load the cell library during synthesis by default - so "
        "Yosys would stop immediately, reporting that "
        "sky130_fd_sc_hd__inv_2 is 'not part of the design'. With the "
        "flag set, the liberty cells are read first as blackboxes: the "
        "names resolve, flatten keeps the cells as real instances, and "
        "the ring reaches the GDS intact."))
    story += data_table(
        ["Config key", "Value", "Why it is set"],
        [
            ["DESIGN_NAME", "t16_top_silicon", "the silicon top - ring included"],
            ["VERILOG_FILES", "dir::src/*.v", "all 7 RTL files, OpenLane 1.x syntax"],
            ["CLOCK_PORT / CLOCK_PERIOD", "clk / 50 ns", "20 MHz - relaxed on purpose"],
            ["FP_SIZING / DIE_AREA", "absolute / 400x400 um", "a roomy first-run die"],
            ["CORE_AREA", "10 10 390 390", "explicit core - one less silent variable"],
            ["PL_TARGET_DENSITY", "0.45", "45% fill - comfortable routing"],
            ["SYNTH_READ_BLACKBOX_LIB", "1", "THE ring-saver - see above"],
        ],
        [0.30, 0.26, 0.44],
        mono_cols=(0,),
        caption_text="Table 14.1 - The generated config.json, key by key.")
    story += h2_block("How the ring was proven to survive", body(
        "For this edition, the exact pass sequence of OpenLane 1.0.2's "
        "synthesis stage was fetched from the OpenLane v1.0.2 source and "
        "replayed against this package with a real Yosys. Two runs were "
        "done. Without the blackbox flag the flow died at the hierarchy "
        "check, exactly as predicted. With it, the full sequence - "
        "hierarchy, flatten, optimize, technology-map - completed with "
        "zero errors, and the final netlist still contained all fifteen "
        "sky130 inverters plus the enable AND gate, with the prescaler "
        "a genuine 8-bit register. That is why this chapter can promise "
        "the ring reaches your GDS: the promise was tested, both ways."))
    story += h2_block("Reading the run and seeing your chip", body(
        "Success prints the line you have seen before: [SUCCESS]: Flow "
        "complete. The artifacts live under designs/telugu_t16_v4/runs/, "
        "with the GDS at results/final/gds/. Open it with KLayout and "
        "spend the minutes it deserves: the gray-blue rectangles are "
        "standard cells, the bright stripes are metal wires, and "
        "somewhere in there are your CPU, your ROM with Fibonacci baked "
        "into gates, and fifteen small inverters chasing each other in a "
        "circle."))
    story += code_block(
        "klayout designs/telugu_t16_v4/runs/RUN_*/results/final/gds/*.gds\n"
        "# reports worth opening afterwards:\n"
        "#   runs/RUN_*/reports/metrics.csv\n"
        "#   runs/RUN_*/logs/floorplan/*.log   (see DIE_AREA / CORE_AREA)",
        label="Tuesday morning - see your chip")


def ch15(story):
    story += h1_block(15, "SPICE Experiments - Proving the Physics", body(
        "The SPICE lab is where the claims of Chapter 12 were measured. "
        "It simulates the actual transistors - real SkyWater sky130 "
        "models, tt corner, bundled in the package - and takes 30 to 60 "
        "minutes for all three experiments, because simulating a "
        "sub-threshold ring point by point is genuinely slow. That "
        "slowness is the physics. Run one at a time if you prefer; each "
        "writes a CSV you can graph or check against the tables here."))
    story += code_block(
        "cd ~/t16/T16_V4/spice\n"
        "bash run_experiments.sh            # all three (30-60 min)\n"
        "python3 run_experiments.py --only 1   # just the VDD sweep\n"
        "ngspice ro_vdd_sweep.spice            # interactive one-point demo",
        label="Monday 2:00 PM - the physics lab")
    story += data_table(
        ["Point", "Measured frequency", "Meaning"],
        SCISSORS_TABLE,
        [0.24, 0.22, 0.54],
        center_cols=(1,),
        caption_text="Table 15.1 - The temperature scissors data "
                     "(measured, tt corner).")
    story += h2_block("Experiment 3 - the body-bias lever, measured",
                      body(
        "Forward body bias lowers the effective threshold voltage: the "
        "source-body junction is biased so the barrier thins, and the "
        "transistor turns on at a lower gate voltage. The measurement "
        "quantifies exactly how much: 159 mV of discount at +0.60 V of "
        "bias. That is real and useful - and it is also the honest "
        "boundary of this lever, a long way from turning a 0.69 V "
        "transistor into a 0.14 V one. Physics gives discounts, not "
        "miracles, and the project's story is stronger for stating it."))
    story += figure(os.path.join(ASSETS, "chart_fbb_vth.png"),
                    "Figure 15.1 - Effective Vth vs forward body bias, "
                    "measured with the bundled sky130 models.",
                    max_h=260)
    story += data_table(
        ["VBS (V)", "Effective Vth", "Note"],
        VTH_TABLE,
        [0.18, 0.20, 0.62],
        center_cols=(0, 1),
        caption_text="Table 15.2 - The body-bias measurements.")
    story += callout(
        "Every number in this chapter regenerates on your machine: the "
        "results CSVs ship in spice/results/ together with a "
        "reproducibility record - five independent spot checks that "
        "matched the bundled data exactly. When you rerun the lab, you "
        "are not trusting anyone's transcript; you are producing your "
        "own.",
        title="Reproducibility is the point")


def ch16(story):
    story += h1_block(16, "TinyTapeout Submission", body(
        "TinyTapeout is the shuttle that makes individual silicon "
        "affordable: many tiny designs share one sky130 wafer run, each "
        "inside a fixed tile with a fixed pin budget, and a GitHub "
        "pipeline builds every GDS the same way yours was built locally. "
        "Your package already contains the adapter - tt_um_telugu_t16.v - "
        "which maps the SoC onto that pin budget."))
    story += data_table(
        ["Pins", "Signal", "Direction", "What it carries"],
        [
            ["clk", "external clock", "in", "CPU clock when CLKSEL=0"],
            ["ui_in[0]", "CLKSEL", "in", "tie statically! 0 external, 1 self-clocked"],
            ["ui_in[7:1]", "GPIO in bits", "in", "readable at address 0x0081"],
            ["uo_out[7:0]", "GPIO out bits", "out", "the program-visible output register"],
            ["uio_out[7:4]", "GPIO out high bits", "out", "output register bits 11:8"],
            ["uio_out[3]", "RO scope tap", "out", "raw ring output for your oscilloscope"],
            ["uio_out[2]", "sleeping", "out", "live WAIT-sleep status"],
            ["uio_out[1]", "halted", "out", "program-complete status"],
            ["uio_out[0]", "P-bit", "out", "live eco/turbo mode"],
            ["rst_n / ena", "reset / enable", "in", "active-low reset; chip enable"],
        ],
        [0.20, 0.20, 0.12, 0.48],
        mono_cols=(0,),
        caption_text="Table 16.1 - The TinyTapeout pin map of your design.")
    story += h2_block("The submission checklist", body(
        "Fork the official TinyTapeout template repository, copy every "
        "file from rtl/ into its src/ directory, set the top module to "
        "tt_um_telugu_t16 in info.yaml, and push. GitHub Actions runs "
        "OpenLane on their infrastructure and produces the submission "
        "GDS. The wrapper uses the same silicon configuration as "
        "t16_top_silicon - real ring, RO/256 sensor, baked program - so "
        "what you verified locally is what they will build. One honest "
        "note: the ena pin is currently accepted but unused by the "
        "wrapper; the harness works either way, and gating the ring on "
        "it remains a documented option for a future revision."))
    story += code_block(
        "1. fork the TinyTapeout template repo on GitHub\n"
        "2. copy rtl/*.v into src/ (all 8 files)\n"
        "3. edit info.yaml:  top_module: tt_um_telugu_t16\n"
        "4. git add . && git commit -m 'T-16 submission'\n"
        "5. git push          -> GitHub Actions builds the GDS\n"
        "6. submit at app.tinytapeout.com (when the next run opens)",
        label="Tuesday evening - the submission path")
    story += callout(
        "The local 400x400 um GDS from Chapter 14 proves you and the "
        "flow. The submission GDS is built by TinyTapeout's own pipeline "
        "inside their tile dimensions - that is normal and expected: "
        "the local run is the rehearsal, the submission is the "
        "performance, and both dance to the same verified RTL.",
        title="Two GDS files, one design")


def ch17(story):
    story += h1_block(17, "Troubleshooting", body(
        "Almost everything that can go wrong in these two days has been "
        "seen before, and the fix is almost always one of eight. Read "
        "this table when something surprises you; find your symptom in "
        "the left column and apply the right one. The deeper principle: "
        "never debug two things at once - get run_sim.sh green again "
        "before touching anything downstream."))
    story += data_table(
        ["Symptom", "Likely cause", "The fix"],
        [
            ["iverilog: command not found", "tool not installed",
             "sudo apt install iverilog"],
            ["Test times out, never halts", "you edited RTL and broke a branch",
             "diff your rtl/ against the package copy; revert the change"],
            ["GPIO values wrong in TEST 1", "hex/asm mismatch after edits",
             "reassemble: python3 tools/t16asm.py sw/program_fib.asm sw/program_fib.hex"],
            ["$readmemh cannot open file", "ran vvp from the wrong directory",
             "run from ~/t16/T16_V4 so sw/... paths resolve"],
            ["Yosys: module sky130_fd_sc_hd__inv_2 not part of the design",
             "config.json lost SYNTH_READ_BLACKBOX_LIB",
             "re-run bash run_openlane.sh (or restore the key: 1)"],
            ["OpenLane cannot find design", "wrong -design name",
             "./flow.tcl -design telugu_t16_v4 exactly"],
            ["Flow fails at floorplan", "DIE_AREA/CORE_AREA strings broken",
             "restore FP_SIZING absolute + both area keys from Table 14.1"],
            ["ngspice produces empty CSV cells", "gave up too early, or deep sub-V point",
             "points below 0.28 V legitimately read dead - that is the physics"],
            ["Docker: permission denied", "user not in docker group",
             "sudo usermod -aG docker $USER, then reopen the terminal"],
        ],
        [0.30, 0.28, 0.42],
        caption_text="Table 17.1 - The nine fixes that cover two days of "
                     "surprises.")
    story += h2_block("The golden rule", body(
        "The package you received passes all four tests exactly as "
        "shipped. That is your restore point. Before any risky "
        "experiment, copy the whole directory aside; when something "
        "breaks, diff against it. Ten seconds of copying saves an "
        "evening of archaeology, and it is exactly how the verification "
        "chain in this book was kept honest in the first place."))
    story += code_block(
        "cp -r ~/t16/T16_V4 ~/t16/T16_V4_known_good   # before experiments\n"
        "diff -r ~/t16/T16_V4_known_good ~/t16/T16_V4 # after any surprise",
        label="The ten-second insurance policy")


def ch18(story):
    story += h1_block(18, "Day-by-Day Execution Guide", body(
        "Everything in the seventeen chapters before this one compresses "
        "into the two tables below. The times are guides, not cages - "
        "but the ORDER matters and is worth keeping, because each block "
        "builds on the previous one's green light. If a block runs long, "
        "the honest move is to finish it before starting the next."))
    story += h2_block("Monday - prove everything once", None)
    story += data_table(
        ["Time", "Task", "Command", "Green light"],
        [
            ["8:00-8:30", "Setup and first verification",
             "bash setup_ubuntu.sh; bash run_sim.sh", "ALL 4 TESTS PASSED"],
            ["8:30-9:30", "Read the chip while it runs",
             "gtkwave build/*.vcd", "you can point at the PC and GPIO"],
            ["9:30-10:30", "Write your first program",
             "edit sw/my.asm; python3 tools/t16asm.py ...", "your values on GPIO"],
            ["10:30-11:00", "Browse the RTL",
             "less rtl/t16_cpu.v rtl/t16_soc.v", "the memory map is familiar"],
            ["1:00-2:00", "Synthesis",
             "bash run_synthesis.sh", "0 errors, cell count written down"],
            ["2:00-4:00", "SPICE physics lab",
             "cd spice; bash run_experiments.sh", "CSVs match Tables 15.1-15.2"],
            ["4:00-6:00", "Free experiment time",
             "bake a program; rerun tests", "still 4/4 after your changes"],
            ["7:00-9:00", "OpenLane setup + flow start",
             "bash run_openlane.sh; make mount; ./flow.tcl ...",
             "[SUCCESS]: Flow complete"],
            ["9:00-10:00", "First look at your chip",
             "klayout .../results/final/gds/*.gds", "you saw your own layout"],
        ],
        [0.13, 0.27, 0.37, 0.23],
        caption_text="Table 18.1 - Monday: simulation, synthesis, physics, "
                     "and the first GDS.")
    story += h2_block("Tuesday - finish, document, submit", None)
    story += data_table(
        ["Time", "Task", "Command", "Green light"],
        [
            ["8:00-9:00", "Re-run the whole suite fresh",
             "bash run_sim.sh", "ALL 4 TESTS PASSED again"],
            ["9:00-10:30", "Study the layout and reports",
             "klayout; cat runs/RUN_*/reports/metrics.csv",
             "area and timing noted in your log"],
            ["10:30-12:00", "Fix anything that bit you",
             "Chapter 17 table", "clean GDS, clean conscience"],
            ["1:00-3:00", "Documentation and evidence",
             "screenshots + README notes", "a stranger could reproduce it"],
            ["3:00-5:00", "TinyTapeout prep",
             "fork template; copy rtl/; edit info.yaml", "Actions pipeline green"],
            ["7:00-8:00", "Push and submit",
             "git push; app.tinytapeout.com", "submission confirmed"],
            ["8:00-9:00", "The final ritual",
             "bash run_sim.sh one last time", "4/4 - you built a chip"],
        ],
        [0.13, 0.27, 0.37, 0.23],
        caption_text="Table 18.2 - Tuesday: polish, document, and submit.")
    story += callout(
        "Two days, honestly scoped, fully scripted. The chip you verify "
        "Monday morning is the chip you submit Tuesday night - the same "
        "RTL, the same tests, the same physics. That continuity is the "
        "quiet superpower of this package.",
        title="The shape of a good two days")


def ch19(story):
    story += h1_block(19, "Glossary", body(
        "The eighteen terms that appear again and again in this book, in "
        "one place, in plain language. When a chapter uses one of these "
        "words as if you own it, this is where it was introduced."))
    story += data_table(
        ["Term", "Plain meaning"],
        [
            ["ASIC", "a chip built for one design, from scratch - not a configurable FPGA"],
            ["RTL", "register-transfer level: Verilog that describes behavior, before gates"],
            ["Synthesis", "turning RTL into a network of logic gates"],
            ["Netlist", "the gate network: which gates, wired how"],
            ["Standard cell", "a predesigned gate from the foundry library (nand, inv, dff...)"],
            ["sky130", "the SkyWater 130 nm open-source process this chip targets"],
            ["PDK", "process design kit: the foundry's files describing sky130 to tools"],
            ["GDSII (GDS)", "the final layout file - polygons of metal and silicon"],
            ["Floorplan", "drawing the die and core rectangles before placing cells"],
            ["Placement / routing", "arranging cells; wiring them in metal layers"],
            ["CTS", "clock tree synthesis: distributing the clock to every flip-flop"],
            ["DRC / LVS", "design-rule check; layout-versus-schematic equivalence check"],
            ["VCD", "value-change dump: the file GTKWave reads as waveforms"],
            ["Testbench", "the harness that drives the design and checks the answers"],
            ["Sub-threshold", "operating below Vth: exponentially slower, radically lower power"],
            ["ITD", "inverse temperature dependence: hot sub-threshold chips run faster"],
            ["Ring oscillator", "odd loop of inverters that beats at a physics-set speed"],
            ["TinyTapeout", "the shared-shuttle service that makes one chip affordable"],
        ],
        [0.22, 0.78],
        caption_text="Table 19.1 - The eighteen terms of the project.")


def appendix(story):
    story += h1_block(20, "Quick Reference Card", body(
        "The one page to keep open all day. Every command of the two-day "
        "sprint, the address map, the receipts, and the numbers worth "
        "remembering - condensed from the eighteen chapters so you never "
        "have to hunt for them mid-flow."),
        kicker="APPENDIX A")
    story += code_block(
        "bash setup_ubuntu.sh        # 1. verify the toolchain\n"
        "bash run_sim.sh             # 2. ALL 4 TESTS MUST PASS\n"
        "gtkwave build/tb_t16_soc.vcd# 3. watch Fibonacci happen\n"
        "bash run_synthesis.sh       # 4. gate count, 0 errors\n"
        "cd spice && bash run_experiments.sh   # 5. real physics (30-60m)\n"
        "bash run_openlane.sh        # 6. stage the flow (writes config)\n"
        "cd ~/OpenLane && make mount # 7. enter the container\n"
        "./flow.tcl -design telugu_t16_v4      # 8. the GDS run\n"
        "klayout designs/telugu_t16_v4/runs/RUN_*/results/final/gds/*.gds",
        label="The whole two days in nine commands")
    story += data_table(
        ["Thing", "Value"],
        [
            ["Fibonacci GPIO sequence", "1 1 2 3 5 8 13 21 34 55 (0x0037 last)"],
            ["ISA test RAM signature", "0x0011 0x000A 0x0008 0x000E 0x0006 0x000C 0x0FF0 0xFFF0 0x0011 0xA5A5 0x0077"],
            ["ISA test GPIO", "0x600D ('GOOD')"],
            ["Eco receipt (cool + woke)", "0xEC01"],
            ["Turbo receipt (hot + raced)", "0x700C"],
            ["Heartbeat period", "32,768 CPU cycles (TIMER bit 15)"],
            ["Ring alive from", "0.28 V (4.4 kHz) to 1.8 V (1.33 GHz)"],
            ["Hot sub-threshold speedup", "12.2x at 0.30 V (27 C to 85 C)"],
            ["Body-bias Vth discount", "159 mV at VBS = +0.60 V"],
            ["Test 4 ring edges (sim)", "2,288 rising edges, zero external clock"],
        ],
        [0.40, 0.60],
        mono_cols=(1,),
        caption_text="Table A.1 - The numbers worth remembering.")
    story += data_table(
        ["Address", "Peripheral"],
        [
            ["0x0000-0x007F", "RAM (128 words)"],
            ["0x0080 / 0x0081", "GPIO OUT / GPIO IN"],
            ["0x0082 / 0x0083", "TIMER / SENSOR"],
            ["0x0084 / 0x0085", "P-bit (MSR) / WAIT"],
        ],
        [0.40, 0.60],
        mono_cols=(0,),
        caption_text="Table A.2 - The memory map, once more.")
    story += h2_block("Where the evidence lives", body(
        "Every claim in this book points at a file you can open. When you "
        "write your project page, README or submission notes, cite the "
        "artifacts - not the assertions. The table below is that map: the "
        "verification trail of the whole two days, in one place, so a "
        "stranger can reproduce or audit any number in this guide."))
    story += data_table(
        ["Claim", "The file that proves it"],
        [
            ["All 4 tests pass, exactly as documented",
             "docs/expected_output.txt + build/log_*.txt (fresh run)"],
            ["The package is byte-complete and untampered",
             "MANIFEST.txt (SHA-256 of all 56 files; sha256sum -c)"],
            ["The physics numbers (heart curve, scissors, Vth)",
             "spice/results/*.csv + the reproducibility record"],
            ["The program in silicon is the tested program",
             "rtl/t16_rom.v baked words + tools/bake_rom.py round-trip"],
            ["The OpenLane config is the verified one",
             "openlane/config.json (SYNTH_READ_BLACKBOX_LIB = 1)"],
            ["Every edit made to V4, and why",
             "EDITS_AND_VERIFICATION.md (the accountability file)"],
        ],
        [0.42, 0.58],
        caption_text="Table A.3 - The evidence map: claim to artifact.")
    story += callout(
        "Two days from now, the strongest sentence you will be able to "
        "write is also the simplest: 'I verified it, here is the file.' "
        "Keep the artifacts, keep the logs, and the chip you ship will "
        "be as honest as the one you simulated.",
        title="The last word")
