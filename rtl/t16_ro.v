// ============================================================================
//  T-16 RING OSCILLATOR  ("the physics heart")  —  V4
//  File    : rtl/t16_ro.v
//  Adapted from V2. 15-inverter ring built from sky130 standard cells.
//
//  At 1.8V: hundreds of MHz. As VDD drops below Vth (~0.45V), it keeps
//  oscillating in SUB-THRESHOLD — exponentially slower but alive.
//  Its frequency INCREASES with temperature in sub-threshold (ITD) —
//  this is what the P-bit software reads via the SENSOR counter.
//
//  USE_RO=1 (tapeout): structural sky130 cell ring
//  USE_RO=0 (sim/FPGA): replaced by external ro_sim_clk
//
//  Project : TELUGU T-16 V4.1 | License : Apache-2.0
// ============================================================================

`timescale 1ns / 1ps

module t16_ro #(
    parameter integer USE_RO = 0,   // V4.1: default 0 (sim-safe). Silicon tops pass 1.
    parameter integer STAGES = 15       // inverters (keep odd!)
) (
    input  wire ena,
    input  wire ro_sim_clk,
    output wire ro_out
);

generate
if (USE_RO) begin : g_ring

    wire [STAGES:0] n;
    wire and_out;

    (* dont_touch = "true" *)
    sky130_fd_sc_hd__and2_0 u_en (
        .A(n[STAGES]),
        .B(ena),
        .X(and_out)
    );

`ifdef T16_SIM
    // Simulation-only deterministic ring starter: hold ring low
    // until the chain settles, then release for clean oscillation.
    reg sim_start = 1'b0;
    initial begin
        #(STAGES * 2 + 10) sim_start = 1'b1;
    end
    assign n[0] = sim_start ? and_out : 1'b0;
`else
    assign n[0] = and_out;
`endif

    genvar i;
    for (i = 0; i < STAGES; i = i + 1) begin : g_inv
        (* dont_touch = "true" *)
        sky130_fd_sc_hd__inv_2 u_inv (
            .A(n[i]),
            .Y(n[i+1])
        );
    end

    assign ro_out = n[STAGES];

end else begin : g_ext
    // Sim / FPGA: ring replaced by external deterministic clock
    assign ro_out = ro_sim_clk;
end
endgenerate

endmodule
