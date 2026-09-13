// ============================================================================
//  T-16 GPIO  ("the hands")  —  V4
//  File    : rtl/t16_gpio.v
//  One 16-bit output latch. On real silicon these become actual pins.
//  Project : TELUGU T-16 V4.1 | License : Apache-2.0
// ============================================================================

`timescale 1ns / 1ps

module t16_gpio (
    input  wire        clk,
    input  wire        we,
    input  wire [15:0] din,
    output wire [15:0] dout,
    output wire [15:0] pins_out
);

    reg [15:0] out_lat;

    always @(posedge clk) begin
        if (we)
            out_lat <= din;
    end

    assign pins_out = out_lat;
    assign dout     = out_lat;

endmodule
