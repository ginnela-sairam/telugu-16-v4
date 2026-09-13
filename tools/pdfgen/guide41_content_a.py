#!/usr/bin/env python3
"""T-16 V4.1 Master Guide content - chapters 1-9."""
import os

from guide41_lib import (S, Spacer, body, bullets, callout, code_block,
                          data_table, figure, h1_block, h2_block, h3_block,
                          stat_row)

PKG = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ASSETS = os.path.join(PKG, "docs")

EXPECTED_OUTPUT = """  ===================================================
   T-16 V4.1  -  Full Verification Suite
   (4 tests: Fibonacci + ISA + P-bit + Silicon config)
  ===================================================

  [ OK ] GPIO write #1 = 0x0001  (Fibonacci #1)
  [ OK ] GPIO write #2 = 0x0001  (Fibonacci #2)
  [ OK ] GPIO write #3 = 0x0002  (Fibonacci #3)
  ...
  [ OK ] GPIO write #10 = 0x0037 (Fibonacci #10)
  [ OK ] CPU reached HALT after 68 clock cycles.
  [ OK ] GPIO was written exactly 10 times.
   *** TEST 1 PASSED - T-16 COMPUTES CORRECTLY ***

  [ OK ] CPU reached HALT after 59 clock cycles.
  [ OK ] RAM[0] = 0x0011 ... RAM[10] = 0x0077  (all 11 match)
  [ OK ] GPIO = 0x600D  ('GOOD')
   *** TEST 2 PASSED - ALL 14 INSTRUCTIONS OK ***

  [ OK ] PHASE 1: CPU reached HALT after 32777 cycles (eco, slept)
  [ OK ] RAM[2] (P-bit readback) = 0x0000  (eco mode chosen)
  [ OK ] CPU entered WAIT sleep - the power saver works.
  [ OK ] CPU woke on the TIMER[15] heartbeat.
  [ OK ] GPIO = 0xEC01  (ECO marker + the wake-up receipt)
  [ OK ] PHASE 2: RAM[2] = 0x0001 (turbo), no sleep, GPIO = 0x700C
   *** TEST 3 PASSED - P-BIT SYSTEM WORKS ***

  [ OK ] PHASE A: all 10 Fibonacci numbers correct (baked ROM).
  [ OK ] PHASE B: CPU reached HALT - SELF-CLOCKED!
  [ OK ] PHASE B: all 10 Fibonacci numbers correct again.
  [ OK ] Ring oscillator total rising edges: 2288
   *** TEST 4 PASSED - SILICON CONFIG WORKS ***

  *** ALL 4 TESTS PASSED - T-16 V4.1 VERIFIED ***"""


def ch1(story):
    story += h1_block(1, "What This Project Is", body(
        "This book is the complete operating manual for the TELUGU T-16: a "
        "16-bit microprocessor you designed, verified, and prepared for real "
        "silicon using only open-source tools. It exists for one purpose - to "
        "carry you through the final two working days (Monday and Tuesday) "
        "from a freshly-unzipped package to a GDSII layout file that could, "
        "in principle, be manufactured. Every command you will type, every "
        "file you will open, and every number you should expect to see is "
        "written down here. Nothing is left to memory or luck."), body_start=True)
    story += body(
        "The T-16 is not a toy even though it is small. It has a clean "
        "single-cycle CPU with eight 16-bit registers and fourteen verified "
        "instructions, 256 words of program ROM, 128 words of data RAM, "
        "memory-mapped GPIO, a free-running timer, a ring-oscillator sensor, "
        "and the P-bit - the thermal-adaptive control idea that makes this "
        "chip personal to you. The same RTL that passes all four test "
        "suites in simulation is the exact RTL that the OpenLane flow turns "
        "into a physical layout. What you simulate is what you ship.")
    story += stat_row([
        ("16-bit", "data path, registers, and bus width"),
        ("14", "verified instructions in the ISA"),
        ("4 / 4", "test suites passing end to end"),
        ("15", "sky130 inverters in the on-die ring"),
    ])
    story += h2_block("The honest scope of these two days", body(
        "The goal of Monday and Tuesday is <b>not</b> to manufacture a chip "
        "or to break a world voltage record. Fabrication takes months and "
        "money, and the true sub-threshold floor of this design - honestly "
        "measured with real SPICE physics in Chapter 12 - is around 0.28 V, "
        "not 0.14 V. What these two days deliver is the strongest thing an "
        "individual engineer can actually deliver: a fully verified, fully "
        "documented, reproducible open-source chip package. You will finish "
        "with a GDS layout you can open in KLayout with your own eyes, a "
        "complete evidence trail, and a submission-ready TinyTapeout "
        "wrapper. That is a real and rare achievement - and it is within "
        "reach precisely because it is honestly scoped."))
    story += h2_block("What makes Version 4 different", body(
        "Three earlier versions taught the lessons that shaped this one. "
        "Version 1 drowned in files nobody could navigate. Version 2 fixed "
        "the structure but left questions unanswered. Version 3 proved the "
        "core CPU. Version 4 is the first version that puts everything "
        "together - the proven CPU, the ring oscillator physics, the "
        "self-clocked record experiment, the P-bit, and a two-day runbook "
        "in one package - and it is the first version in which every "
        "claim has been re-verified with real tools, not asserted."))
    story += data_table(
        ["Feature", "Where it came from", "Why it matters to you"],
        [
            ["Proven V3 CPU core", "carried forward unchanged",
             "the ISA logic is already trusted - nothing new to break"],
            ["On-die ring oscillator", "V2 physics work, rebuilt for V4",
             "the chip can clock itself with no external clock at all"],
            ["P-bit thermal control", "your original idea, first truly tested in V4.1",
             "the chip reads its own sensor and picks eco or turbo"],
            ["Baked-ROM silicon flow", "new in V4.1",
             "the program becomes real gates that survive Docker synthesis"],
            ["Four-stage test suite", "new in V4.1",
             "machine proof that the silicon configuration boots"],
        ],
        [0.24, 0.36, 0.40],
        caption_text="Table 1.1 - What Version 4 is made of.")
    story += callout(
        "Open the package, run one command, and watch all four tests pass. "
        "From that moment on, this book is your map: each chapter covers one "
        "stage of the flow, in the order you will actually meet it on "
        "Monday and Tuesday.",
        title="How to read this book")


def ch2(story):
    story += h1_block(2, "What a Chip Is - The Basics", body(
        "A chip (an integrated circuit) is a rectangle of silicon with "
        "transistors and wires etched onto its surface by a factory. "
        "Transistors are microscopic switches; wires connect them. A "
        "processor like the T-16 is nothing supernatural - it is just "
        "several thousand of these switches arranged so that the pattern "
        "of ON and OFF follows the rules of a program. The magic of digital "
        "design is that if you get the arrangement right, arithmetic, "
        "memory, and decisions all fall out of it."))
    story += body(
        "You already know the FPGA world: you describe logic in Verilog, "
        "and Vivado maps it onto a prefabricated grid of configurable "
        "blocks. An ASIC (application-specific integrated circuit) is the "
        "other world: there is no pre-made grid. Every gate is placed "
        "individually and every wire is routed individually for your "
        "design and your design alone. The factory (a foundry, such as "
        "SkyWater for the sky130 process) receives one file - the GDSII "
        "layout - and returns physical silicon. The GDS file is therefore "
        "the final artifact of this whole project: everything in this book "
        "exists to produce it and to prove it correct.")
    story += data_table(
        ["Concept", "In the FPGA world you know", "In the ASIC world of this project"],
        [
            ["Design language", "Verilog (same)", "Verilog (same)"],
            ["Who builds it", "Vivado, on a prefabricated chip",
             "OpenLane, from scratch for this design"],
            ["Basic building block", "LUTs and flip-flops",
             "standard cells: nand, nor, dff, inv from the sky130 library"],
            ["Clock", "an input pin on the FPGA board",
             "your own on-die ring oscillator (or an input pin)"],
            ["Result file", "bitstream (secret format)", "GDSII (open format, 40+ years old)"],
            ["Cost of one copy", "already paid (the board)",
             "shared shuttle run, e.g. TinyTapeout (tens of dollars)"],
        ],
        [0.20, 0.38, 0.42],
        caption_text="Table 2.1 - The two worlds, side by side.")
    story += h2_block("The journey of your Verilog", body(
        "Your Verilog travels a five-stage pipeline of tools, and each "
        "stage hands a file to the next: <b>Icarus Verilog</b> simulates "
        "the RTL and proves behavior; <b>GTKWave</b> shows the waveforms; "
        "<b>Yosys</b> synthesizes RTL into generic gates; <b>OpenLane</b> "
        "(with its own Yosys, plus placement, routing and signoff engines) "
        "maps those gates onto real sky130 standard cells and produces the "
        "GDSII; and <b>KLayout</b> lets you see the result. The packaged "
        "scripts run each stage in exactly this order, so the pipeline is "
        "something you will watch happen rather than memorize."))
    story += figure(os.path.join(ASSETS, "diagram_flow.png"),
                    "Figure 2.1 - From an idea to silicon: the five-tool "
                    "pipeline of this project.",
                    max_h=300)


def ch3(story):
    story += h1_block(3, "The T-16 Architecture", body(
        "The T-16 is a system-on-chip built from eight small Verilog "
        "modules, each with one job. The CPU executes one instruction per "
        "clock cycle. The ROM holds the program. The RAM holds variables. "
        "The GPIO latch drives the output pins. The ring oscillator beats "
        "at a speed set by physics - supply voltage and temperature. The "
        "prescaler divides that beat down to a usable CPU clock. The "
        "timer and sensor counters let software observe time and physics. "
        "And the P-bit register is the one-bit mode switch that ties it "
        "all together into a thermal-adaptive machine."))
    story += figure(os.path.join(ASSETS, "diagram_architecture.png"),
                    "Figure 3.1 - The T-16 SoC: CPU, memories, peripherals, "
                    "and the ring-oscillator heart.",
                    max_h=310)
    story += h2_block("The memory map - every peripheral has an address",
                      body(
        "The CPU talks to everything through a single 16-bit bus. To read "
        "or write a peripheral, software simply loads or stores to its "
        "address. This memory-mapped design is why the CPU needed zero "
        "changes from V3: peripherals are just addresses, and the ISA "
        "already knows how to use addresses."))
    story += data_table(
        ["Address", "Name", "Direction", "What it does"],
        [
            ["0x0000-0x007F", "RAM", "read/write",
             "128 words of scratch memory"],
            ["0x0080", "GPIO OUT", "read/write",
             "write = set the 16 output pins; read = see them"],
            ["0x0081", "GPIO IN", "read", "reads the 16 input pins"],
            ["0x0082", "TIMER", "read", "free-running 16-bit counter"],
            ["0x0083", "SENSOR", "read", "counts ring-oscillator pulses"],
            ["0x0084", "MSR / P-bit", "read/write",
             "bit 0 = P: 0 eco, 1 turbo"],
            ["0x0085", "WAIT", "write",
             "sleep request - freezes the CPU until the heartbeat if P=0"],
            ["anything else", "(black hole)", "-", "writes dropped, reads 0"],
        ],
        [0.17, 0.15, 0.13, 0.55],
        mono_cols=(0,),
        caption_text="Table 3.1 - The complete memory map. These seven "
                     "addresses are the whole peripheral interface.")
    story += h2_block("Two clock sources, one mux", body(
        "The clksel input chooses the CPU clock. With clksel = 0 the CPU "
        "runs from the external clk pin - the friendly, debuggable mode. "
        "With clksel = 1 the CPU clock is RO/32, taken from bit 4 of the "
        "prescaler that the ring oscillator drives - the self-clocked "
        "mode that needs no external clock at all. The rule is simple and "
        "important: <b>tie clksel statically before releasing reset, and "
        "never switch it while the chip is running</b>. A clock mux that "
        "switches mid-run can clip a clock pulse and corrupt CPU state."))
    story += callout(
        "In self-clocked mode the prescaler must keep counting even while "
        "reset is held, because it IS the clock. The V4.1 fix removed the "
        "prescaler's reset precisely for this reason - Chapter 9's TEST 4 "
        "proves the chip boots with zero external clock edges.",
        title="Why the prescaler has no reset")


def ch4(story):
    story += h1_block(4, "Your Tools - What Each Program Does", body(
        "Your Ubuntu machine already has the complete open-source ASIC "
        "toolchain installed. This chapter is the map of which program "
        "opens which file, so nothing on your screen is ever a stranger. "
        "The one rule that removes most confusion: <b>every tool consumes "
        "the previous tool's output</b>. You never open a file with the "
        "wrong program if you remember the pipeline order."))
    story += data_table(
        ["Tool", "It opens", "It produces", "When you use it"],
        [
            ["Icarus Verilog (iverilog, vvp)", ".v RTL + testbenches",
             "console output + .vcd waveforms", "all day Monday"],
            ["GTKWave", ".vcd waveform files", "visual signal traces",
             "after each simulation"],
            ["Python 3 (t16asm.py, bake_rom.py)", ".asm programs, .hex",
             ".hex machine code, baked ROM words", "writing programs"],
            ["Yosys", "RTL Verilog", "gate-level netlist + statistics",
             "Monday afternoon"],
            ["ngspice", "SPICE transistor decks", "CSV physics measurements",
             "Monday afternoon"],
            ["OpenLane 1.0.2 (Docker)", "RTL + config.json",
             "the GDSII layout + reports", "Monday evening / Tuesday"],
            ["KLayout", ".gds layout files", "your chip, visually",
             "after the flow"],
            ["git + GitHub", "the whole package", "the TinyTapeout repo",
             "Tuesday evening"],
        ],
        [0.26, 0.24, 0.27, 0.23],
        caption_text="Table 4.1 - The eight tools of the two-day sprint.")
    story += h2_block("About Vivado (the question you asked)", body(
        "Vivado is an FPGA tool: it maps Verilog onto configurable hardware "
        "you already own. It cannot produce a GDSII for an ASIC foundry, "
        "so it has no role in this package's flow. Your Vivado knowledge "
        "is not wasted - the Verilog you write is identical - but for "
        "these two days, everything happens in Ubuntu with the tools "
        "above. If you ever want to see the T-16 on your FPGA board for "
        "fun, the older V2 package contains a Vivado project recipe; it "
        "is optional and not part of the silicon path."))
    story += callout(
        "Nothing else needs to be installed. Run bash setup_ubuntu.sh "
        "first thing Monday and it will verify every tool in Table 4.1 "
        "and tell you exactly what (if anything) is missing.",
        title="You already have everything")


def ch5(story):
    story += h1_block(5, "Setup - Getting Ready", body(
        "Monday morning begins with fifteen minutes of setup. The package "
        "is designed so that setup is one script, verification is one "
        "script, and everything after that is reading waveforms and "
        "running flows. Work inside Ubuntu (WSL), not on the Windows "
        "side: the Linux filesystem is many times faster, and every "
        "tool lives there anyway."))
    story += code_block(
        "cd ~/t16/T16_V4          # wherever you unzipped the package\n"
        "bash setup_ubuntu.sh     # copies to ~/t16, fixes line endings,\n"
        "                         # checks every tool, prints what's missing\n"
        "cd ~/t16/T16_V4\n"
        "bash run_sim.sh          # THE moment of truth - about one minute",
        label="Monday 8:00 AM - the two commands that start everything")
    story += h2_block("What setup_ubuntu.sh actually does", body(
        "The script is deliberately boring. It copies the package into "
        "~/t16/T16_V4 on the Linux filesystem (if you unzipped it "
        "elsewhere), converts any Windows line endings, marks the runner "
        "scripts executable, and then walks a checklist of every tool - "
        "iverilog, vvp, gtkwave, yosys, ngspice, python3, make, git, "
        "klayout, and OpenLane/Docker awareness. Anything missing is "
        "printed with the exact apt command to install it. When the "
        "script says all required tools are present, you are ready for "
        "the rest of the day."))
    story += bullets([
        "Files copied to <b>~/t16/T16_V4</b> - Linux-native speed",
        "Line endings normalized - no Windows carriage-return surprises",
        "All runner scripts made executable",
        "Tool checklist with per-tool versions and fix commands",
        "OpenLane located automatically (or set OPENLANE_DIR=/path and re-run)",
    ])


def ch6(story):
    story += h1_block(6, "Understanding Every File", body(
        "The whole package is 56 files, and every one of them has exactly "
        "one reason to exist. Nothing ships that you cannot open and "
        "read. This table is the complete map - when a command mentions a "
        "file, come back here and remind yourself what it is."))
    story += data_table(
        ["Path", "What it is"],
        [
            ["rtl/t16_cpu.v", "the brain - 16-bit single-cycle CPU (V3 core, unchanged)"],
            ["rtl/t16_soc.v", "the whole chip - CPU + memories + peripherals + clock mux"],
            ["rtl/t16_rom.v", "program ROM: baked words for silicon, .hex override for sim"],
            ["rtl/t16_ram.v", "128-word data RAM"],
            ["rtl/t16_gpio.v", "16-bit output pin latch"],
            ["rtl/t16_ro.v", "the ring oscillator: 15 sky130 inverters + enable AND"],
            ["rtl/t16_top_silicon.v", "the silicon top (USE_RO=1, baked ROM) - what OpenLane builds"],
            ["rtl/tt_um_telugu_t16.v", "TinyTapeout pin-budget wrapper (same silicon config)"],
            ["tb/tb_t16_soc.v", "TEST 1: Fibonacci on GPIO"],
            ["tb/tb_t16_isa.v", "TEST 2: every instruction exercised, RAM signature checked"],
            ["tb/tb_t16_pbit.v", "TEST 3: P-bit eco/turbo decision, sleep and wake proof"],
            ["tb/tb_t16_silicon.v", "TEST 4: baked ROM + real ring + self-clocked boot"],
            ["tb/sky130_shims.v", "2 ns behavioral models of the two ring cells (sim only)"],
            ["sw/*.asm, sw/*.hex", "programs and their assembled machine code"],
            ["tools/t16asm.py", "the assembler: .asm to .hex"],
            ["tools/bake_rom.py", "bakes a .hex program into rtl/t16_rom.v for silicon"],
            ["run_sim.sh", "runs all four tests and prints the verdict"],
            ["run_synthesis.sh", "Yosys gate-count / area report"],
            ["run_openlane.sh", "copies RTL + writes config.json into OpenLane"],
            ["setup_ubuntu.sh", "the Monday-morning setup script"],
            ["spice/", "the transistor-physics lab + bundled sky130 models"],
            ["docs/", "this book's source, the expected-output transcript, diagrams"],
            ["openlane/", "the reference copies that run_openlane.sh writes here"],
        ],
        [0.34, 0.66],
        mono_cols=(0,),
        caption_text="Table 6.1 - The complete file map (essentials; the "
                     "manifest lists every file with its SHA-256).")
    story += callout(
        "Two files deserve a mental bookmark: rtl/t16_rom.v, because the "
        "program inside it is baked into gates for silicon, and "
        "run_sim.sh, because it is the single source of truth for whether "
        "the whole package is healthy. If run_sim.sh passes, everything "
        "downstream has a solid foundation.",
        title="The two files to bookmark")


def ch7(story):
    story += h1_block(7, "The Instruction Set", body(
        "Fourteen instructions, three formats, no surprises. The register "
        "form packs opcode, three register numbers and a shift function "
        "into one 16-bit word; the immediate form carries a signed 9-bit "
        "constant; the branch form uses the immediate as a relative "
        "offset. Every instruction executes in exactly one clock cycle - "
        "there is no pipelining, which is precisely why the core is so "
        "verifiable and so friendly to low voltages."))
    story += data_table(
        ["Op", "Mnemonic", "Form", "Meaning"],
        [
            ["0x0", "ADD Rd, Ra, Rb", "reg", "Rd = Ra + Rb"],
            ["0x1", "SUB Rd, Ra, Rb", "reg", "Rd = Ra - Rb"],
            ["0x2", "AND Rd, Ra, Rb", "reg", "Rd = Ra AND Rb (bitwise)"],
            ["0x3", "OR  Rd, Ra, Rb", "reg", "Rd = Ra OR Rb"],
            ["0x4", "XOR Rd, Ra, Rb", "reg", "Rd = Ra XOR Rb"],
            ["0x5/0", "SLL Rd, Ra, Rb", "reg+func", "Rd = Ra shifted left by Rb"],
            ["0x5/1", "SRL Rd, Ra, Rb", "reg+func", "Rd = Ra shifted right (zero fill)"],
            ["0x5/2", "SRA Rd, Ra, Rb", "reg+func", "Rd = Ra shifted right (sign kept)"],
            ["0x6", "LDI Rd, imm9", "imm", "Rd = imm9 (signed -256..+255)"],
            ["0x7", "LDM Rd, Ra, Rb", "reg", "Rd = MEM[Ra + Rb]"],
            ["0x8", "STM Rd, Ra, Rb", "reg", "MEM[Ra + Rb] = Rd"],
            ["0xA", "BEQZ Rd, label", "branch", "if Rd == 0, PC += offset"],
            ["0xB", "BNEZ Rd, label", "branch", "if Rd != 0, PC += offset"],
            ["0xC", "JAL Rd, label", "branch", "Rd = return address; PC jumps"],
            ["0xD", "JR  Rd", "reg", "PC = Rd (return from call)"],
            ["0xF", "HALT", "-", "freeze the CPU forever"],
        ],
        [0.09, 0.24, 0.12, 0.55],
        mono_cols=(1,),
        center_cols=(0, 2),
        caption_text="Table 7.1 - The complete ISA. Sixteen opcode slots "
                     "exist; two stay unused (0x9, 0xE).")
    story += h2_block("The tricks worth knowing", body(
        "The ISA has no compare instruction and no NOP - and needs "
        "neither. A compare is SUB into a scratch register followed by "
        "BEQZ/BNEZ. A NOP is SLL R0, R0, R0 or ADD R0, R0, R0, which "
        "writes the always-zero register harmlessly. The signed-compare "
        "idiom used by the P-bit program is the most elegant trick in "
        "the set: subtract, shift the result right arithmetically by 15, "
        "and the register becomes 0xFFFF exactly when the difference was "
        "negative. One BNEZ later, you have a full signed comparison."))
    story += code_block(
        "SUB  R5, R2, R3      ; R5 = sensor - threshold\n"
        "LDI  R4, 15          ; the shift amount\n"
        "SRA  R4, R5, R4      ; 0xFFFF if negative, 0x0000 if not\n"
        "BNEZ R4, cooler_path ; negative means sensor < threshold",
        label="The signed-compare idiom (extracted from program_pbit.asm)")


def ch8(story):
    story += h1_block(8, "Writing Your Own Programs", body(
        "The assembler is a single Python file and its language is "
        "readable in one sitting. Comments start with a semicolon; labels "
        "end with a colon; numbers can be decimal, negative or hex. The "
        "assembler also supports the tiny conveniences that make assembly "
        "bearable: NOP as a pseudo-instruction, and expressions where a "
        "register is expected written as [Ra+Rb] for clarity in loads "
        "and stores."))
    story += code_block(
        "; my_first.asm - blink a counter on the GPIO pins\n"
        "        LDI   R4, 0x80      ; GPIO OUT address\n"
        "        LDI   R0, 0         ; counter\n"
        "        LDI   R7, 1         ; increment\n"
        "loop:   STM   R0, [R4+R6]   ; write counter to pins (R6=0)\n"
        "        ADD   R0, R0, R7    ; counter++\n"
        "        LDI   R3, 200       ; delay length\n"
        "wait:   SUB   R3, R3, R7    ; busy-wait countdown\n"
        "        BNEZ  R3, wait\n"
        "        BEQZ  R6, loop      ; R6 is always 0 -> jump\n"
        "        HALT",
        label="A complete, correct T-16 program in ten lines")
    story += h2_block("Assemble, simulate, iterate", body(
        "The edit-simulate loop is two commands. Assemble the program "
        "into a .hex file, then point the simulation at it by changing "
        "one line in a testbench copy - or simply replace the INIT_FILE "
        "default. In simulation mode the ROM loads the .hex file fresh "
        "at time zero, so iteration is instant: edit, assemble, rerun, "
        "read the console, open the waveform."))
    story += code_block(
        "python3 tools/t16asm.py sw/my_first.asm sw/my_first.hex\n"
        "iverilog -g2012 -o build/my_sim rtl/*.v tb/tb_t16_soc.v\n"
        "vvp build/my_sim | tee build/my_log.txt\n"
        "gtkwave build/tb_t16_soc.vcd",
        label="The two-command edit-simulate loop")
    story += h2_block("When a program is destined for silicon", body(
        "Simulation reads the .hex file, but silicon cannot: inside the "
        "OpenLane Docker container the relative path does not even exist. "
        "That is why V4.1 has two ROM modes. For silicon you bake the "
        "program words directly into rtl/t16_rom.v between two markers, "
        "and every word you do not bake defaults to HALT - a total "
        "failure still stops safely instead of executing garbage. Bake "
        "with the tool, then rerun the flow:"))
    story += code_block(
        "python3 tools/bake_rom.py sw/my_first.hex   # bake your program\n"
        "bash run_sim.sh                             # tests still pass\n"
        "bash run_openlane.sh                        # re-copy + re-config\n"
        "# then inside the OpenLane container:\n"
        "#   ./flow.tcl -design telugu_t16_v4 -tag myfirst",
        label="Baking a new program into the silicon ROM")


def ch9(story):
    story += h1_block(9, "Running Simulations", body(
        "One command runs the entire verification suite. It compiles and "
        "executes four testbenches, prints per-test verdicts, and finishes "
        "with the single line that means the package is healthy. The "
        "suite takes about a minute - most of it in TEST 4's Phase B, "
        "where the CPU runs at true ring speed, which is slow by design "
        "because the ring is slow."))
    story += code_block(EXPECTED_OUTPUT,
                        label="bash run_sim.sh - the transcript you must see "
                              "(condensed; the full version is in "
                              "docs/expected_output.txt)")
    story += h2_block("What each test actually proves", body(
        "TEST 1 proves arithmetic and the CPU-ROM-RAM-GPIO path: ten "
        "Fibonacci numbers appear on the output pins in order, and the "
        "CPU halts cleanly after 68 cycles. TEST 2 is the instruction "
        "audit: a purpose-built program exercises every instruction and "
        "leaves an eleven-word RAM signature that must match exactly. "
        "TEST 3 is the behavioral proof of the P-bit idea - a slow ring "
        "means a cool chip, so the program must choose eco, really sleep, "
        "really wake, and leave the 0xEC01 receipt; a fast ring means "
        "hot, so turbo, no sleep, 0x700C. TEST 4 proves the silicon "
        "configuration itself: the baked ROM computes correctly, the "
        "behavioral ring beats, and then - the flagship - clksel=1 with "
        "zero external clock edges, the CPU drives itself from its own "
        "physics and still computes all ten numbers."))
    story += stat_row([
        ("68", "cycles to HALT in TEST 1"),
        ("32777", "eco-mode cycles in TEST 3 (slept most of them)"),
        ("2288", "ring edges counted in TEST 4"),
        ("4/4", "tests passing - the gate to everything else"),
    ])
    story += h2_block("Reading a failure", body(
        "If a test fails, the transcript names the exact mismatch - the "
        "RAM word, the GPIO value, the missing HALT. The waveforms are "
        "already saved in build/ for exactly this moment. A failure "
        "almost always means an edit broke something since the last "
        "green run; the fastest path back is to diff your change against "
        "the package's copy and revert anything inside the RTL, because "
        "the shipped RTL is frozen and verified. Remember that "
        "expected_output.txt is not a hope - it is the captured transcript "
        "of this exact package passing, so any diff you see is real."))
    story += figure(os.path.join(ASSETS, "diagram_2day.png"),
                    "Figure 9.1 - The two-day map: where the verification "
                    "suite sits in your Monday.",
                    max_h=290)
