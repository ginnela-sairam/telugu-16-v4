// ============================================================================
//  TinyTapeout Wrapper for TELUGU T-16 V4.1
//  File    : rtl/tt_um_telugu_t16.v
//
//  This module adapts the T-16 SoC to TinyTapeout's fixed pin budget:
//
//    ui_in[0]  : CLKSEL — 0=external clock, 1=self-clock from ring osc
//                TIE STATICALLY before releasing reset!
//    ui_in[7:1]: general inputs (read via GPIO_IN address 0x0081)
//    uo_out    : gpio_out[7:0]  (program-visible output register)
//    uio_out   : [7:4]=gpio_out[11:8], [3]=raw RO output (scope tap),
//                [2]=sleeping, [1]=halted, [0]=live P-bit status
//    clk       : external clock (used only when CLKSEL=0)
//    ena       : chip enable
//    rst_n     : active-low reset
//
//  HOW TO USE WITH TINYTAPEOUT TEMPLATE:
//    1. Fork the official TinyTapeout template repo
//    2. Copy all rtl/*.v files into src/
//    3. Set top_module = tt_um_telugu_t16 in info.yaml
//    4. Push — GitHub Actions runs OpenLane → GDS
//    5. Submit at app.tinytapeout.com
//
//  Project : TELUGU T-16 V4.1 | License : Apache-2.0
// ============================================================================

`default_nettype none
`timescale 1ns / 1ps

module tt_um_telugu_t16 (
    input  wire       clk,
    input  wire [7:0] ui_in,
    output wire [7:0] uo_out,
    input  wire [7:0] uio_in,      // unused (reserved by TinyTapeout)
    output wire [7:0] uio_out,
    output wire [7:0] uio_oe,
    input  wire       ena,
    input  wire       rst_n
);

    // Active-high reset for V4 SoC
    wire rst = ~rst_n;

    // GPIO extended to 16 bits (lower 8 from ui_in, upper 8 from uio_in)
    wire [15:0] gpio_in_full = {8'h00, ui_in};
    wire [15:0] gpio_out_full;
    wire        halted_w;
    wire        sleeping_w;
    wire        ro_out_w;
    wire        msr_p_w;

    t16_soc #(
        .ROM_DEPTH  (256),      // 256 instructions
        .RAM_DEPTH  (128),      // 128 words data
        .INIT_FILE  (""),       // program BAKED into rtl/t16_rom.v (V4.1);
                               // regenerate with: python3 tools/bake_rom.py sw/program_fib.hex
        .USE_RO     (1),        // on-die ring oscillator
        .SENSOR_TAP (7)         // RO/256 — safe at any VDD for silicon
    ) u_soc (
        .clk        (clk),
        .rst        (rst),
        .clksel     (ui_in[0]),
        .gpio_in    (gpio_in_full),
        .gpio_out   (gpio_out_full),
        .halted     (halted_w),
        .sleeping   (sleeping_w),
        .ro_sim_clk (1'b0),     // unused when USE_RO=1
        .ro_out_pin (ro_out_w),
        .msr_p_pin  (msr_p_w)
    );

    // Pin mapping
    assign uo_out  = gpio_out_full[7:0];
    assign uio_out = {gpio_out_full[11:8],   // [7:4] high GPIO bits
                      ro_out_w,               // [3]   raw RO output (scope)
                      sleeping_w,             // [2]   sleep status
                      halted_w,               // [1]   halt status
                      msr_p_w};               // [0]   live P-bit
    assign uio_oe  = 8'hFF;                   // all outputs

endmodule

// Restore the default net type so files compiled AFTER this one are not
// affected by the `default_nettype none above (classic multi-file gotcha).
`default_nettype wire
