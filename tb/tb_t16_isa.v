// ============================================================================
//  TESTBENCH 2 — "Does EVERY instruction work?"
//  File    : tb/tb_t16_isa.v
//  Adapted from V3 for V4's SoC interface.
//  Project : TELUGU T-16 V4.1 | License : Apache-2.0
// ============================================================================

`timescale 1ns / 1ps

module tb_t16_isa;

    reg         clk;
    reg         rst;
    reg  [15:0] gpio_in;
    wire [15:0] gpio_out;
    wire        halted;
    wire        sleeping;
    wire        ro_out_pin;
    wire        msr_p_pin;

    t16_soc #(
        .ROM_DEPTH (256),
        .RAM_DEPTH (128),
        .INIT_FILE ("sw/program_isatest.hex"),
        .USE_RO    (0),
        .SENSOR_TAP(2)
    ) dut (
        .clk        (clk),
        .rst        (rst),
        .clksel     (1'b0),
        .gpio_in    (gpio_in),
        .gpio_out   (gpio_out),
        .halted     (halted),
        .sleeping   (sleeping),
        .ro_sim_clk (1'b0),
        .ro_out_pin (ro_out_pin),
        .msr_p_pin  (msr_p_pin)
    );

    initial clk = 1'b0;
    always #5 clk = ~clk;

    // Answer key: RAM signature at HALT
    reg [15:0] expect_ram [0:10];
    integer errors;
    integer n;
    integer k;

    initial begin
        expect_ram[0]=16'h0011; expect_ram[1]=16'h000A; expect_ram[2]=16'h0008;
        expect_ram[3]=16'h000E; expect_ram[4]=16'h0006; expect_ram[5]=16'h000C;
        expect_ram[6]=16'h0FF0; expect_ram[7]=16'hFFF0; expect_ram[8]=16'h0011;
        expect_ram[9]=16'hA5A5; expect_ram[10]=16'h0077;
    end

    initial begin
        $dumpfile("build/tb_t16_isa.vcd");
        $dumpvars(0, tb_t16_isa);

        errors  = 0;
        gpio_in = 16'hA5A5;

        $display("");
        $display("=====================================================");
        $display("  T-16 V4.1  |  TEST 2: full ISA coverage");
        $display("  Every instruction runs; results land in RAM.");
        $display("=====================================================");
        $display("");

        rst = 1'b1;
        repeat (2) @(posedge clk);
        rst = 1'b0;
        $display("  Reset released - running the ISA exercise program...");

        k = 0;
        while (!halted && k < 10000) begin
            @(posedge clk);
            k = k + 1;
        end
        #1;

        if (halted !== 1'b1) begin
            $display("  [FAIL] CPU never reached HALT (timeout).");
            errors = errors + 1;
        end else begin
            $display("  [ OK ] CPU reached HALT after %0d clock cycles.", k);
        end

        $display("  --- RAM signature check ---");
        for (n = 0; n <= 10; n = n + 1) begin
            if (dut.u_ram.mem[n] !== expect_ram[n]) begin
                errors = errors + 1;
                $display("  [FAIL] RAM[%0d] = 0x%04h  (expected 0x%04h)",
                         n, dut.u_ram.mem[n], expect_ram[n]);
            end else begin
                $display("  [ OK ] RAM[%0d] = 0x%04h", n, dut.u_ram.mem[n]);
            end
        end

        $display("  --- GPIO magic check ---");
        if (gpio_out !== 16'h600D) begin
            errors = errors + 1;
            $display("  [FAIL] GPIO = 0x%04h  (expected 0x600D = 'GOOD')", gpio_out);
        end else begin
            $display("  [ OK ] GPIO = 0x600D  ('GOOD')  - shifts and OR built it");
        end

        if (errors == 0) begin
            $display("");
            $display("  ================================================");
            $display("   *** TEST 2 PASSED - ALL 14 INSTRUCTIONS OK ***");
            $display("  ================================================");
        end else begin
            $display("");
            $display("  ************************************************");
            $display("   *** TEST 2 FAILED - %0d error(s) ***", errors);
            $display("  ************************************************");
        end
        $display("");
        $finish;
    end

endmodule
