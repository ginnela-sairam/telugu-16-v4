// ============================================================================
//  T-16 DATA RAM  ("the scratchpad")  —  V4
//  File    : rtl/t16_ram.v
//  128 words x 16 bits of read/write memory. Parameterizable depth.
//  Project : TELUGU T-16 V4.1 | License : Apache-2.0
// ============================================================================

`timescale 1ns / 1ps

module t16_ram #(
    parameter RAM_DEPTH = 128
) (
    input  wire                         clk,
    input  wire                         we,
    input  wire [$clog2(RAM_DEPTH)-1:0] addr,
    input  wire [15:0]                  din,
    output wire [15:0]                  dout
);

    reg [15:0] mem [0:RAM_DEPTH-1];

    always @(posedge clk) begin
        if (we)
            mem[addr] <= din;
    end

    assign dout = mem[addr];

endmodule
