// ============================================================================
//  sky130 Behavioral Shims  —  V4
//  File    : tb/sky130_shims.v
//
//  Tiny behavioral models of the two sky130 standard cells used by the
//  ring oscillator. NOT synthesizable — simulation only.
//  Each gate has a 2ns transport delay to model real propagation.
//
//  Project : TELUGU T-16 V4.1 | License : Apache-2.0
// ============================================================================

`timescale 1ns / 1ps

module sky130_fd_sc_hd__inv_2 (
    input  wire A,
    output wire Y
);
    assign #2 Y = ~A;
endmodule

module sky130_fd_sc_hd__and2_0 (
    input  wire A,
    input  wire B,
    output wire X
);
    assign #2 X = A & B;
endmodule
