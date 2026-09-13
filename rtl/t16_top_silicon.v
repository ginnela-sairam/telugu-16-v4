// ============================================================================
//  T-16 SILICON TOP  ("what actually becomes the layout")  —  V4.1 NEW
//  File    : rtl/t16_top_silicon.v
//
//  WHY THIS FILE EXISTS:
//    The default t16_soc parameters are set for SIMULATION (USE_RO=0:
//    the ring oscillator is replaced by a pretend clock). If you send
//    THAT to OpenLane, the GDS would contain NO ring oscillator — the
//    chip's physics heart, the whole point of the project, would be
//    missing from the silicon.
//
//    This top wrapper configures the SAME proven SoC for silicon:
//      * USE_RO     = 1   -> the real 15-inverter sky130 ring is built
//      * SENSOR_TAP = 7   -> SENSOR counts RO/256 (safe at any VDD)
//      * INIT_FILE  = ""  -> no .hex file to find inside Docker; the
//                            program is BAKED into rtl/t16_rom.v
//                            (regenerate with tools/bake_rom.py)
//
//    The TinyTapeout wrapper (tt_um_telugu_t16.v) does the same thing
//    plus maps signals to TinyTapeout's fixed pin budget. Use THIS top
//    for your local OpenLane GDS run; use the tt_um top for the actual
//    TinyTapeout submission.
//
//  Project : TELUGU T-16 V4.1 | License : Apache-2.0
// ============================================================================

`timescale 1ns / 1ps

module t16_top_silicon (
    input  wire        clk,         // external clock (used when clksel=0)
    input  wire        rst,         // active-high reset
    input  wire        clksel,      // 0 = external clock, 1 = self-clocked
    input  wire [15:0] gpio_in,     // 16 input pins
    output wire [15:0] gpio_out,    // 16 output pins
    output wire        halted,      // 1 = program reached HALT
    output wire        sleeping,    // 1 = CPU in WAIT sleep (eco mode)
    output wire        ro_out_pin,  // raw ring oscillator output (scope tap)
    output wire        msr_p_pin    // live P-bit status (scope tap)
);

    t16_soc #(
        .ROM_DEPTH  (256),
        .RAM_DEPTH  (128),
        .INIT_FILE  (""),           // program baked into t16_rom.v
        .USE_RO     (1),            // BUILD the real sky130 ring
        .SENSOR_TAP (7)             // RO/256 — safe at any VDD
    ) u_soc (
        .clk        (clk),
        .rst        (rst),
        .clksel     (clksel),
        .gpio_in    (gpio_in),
        .gpio_out   (gpio_out),
        .halted     (halted),
        .sleeping   (sleeping),
        .ro_sim_clk (1'b0),         // not used when USE_RO=1
        .ro_out_pin (ro_out_pin),
        .msr_p_pin  (msr_p_pin)
    );

endmodule
