// ============================================================================
//  TESTBENCH 1 — "Does the T-16 compute Fibonacci correctly?"
//  File    : tb/tb_t16_soc.v
//  Adapted from V3 for V4's SoC interface (added clksel, sleeping, etc.)
//  Project : TELUGU T-16 V4.1 | License : Apache-2.0
// ============================================================================

`timescale 1ns / 1ps

module tb_t16_soc;

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
        .INIT_FILE ("sw/program_fib.hex"),
        .USE_RO    (0),          // no ring for this test — deterministic
        .SENSOR_TAP(2)
    ) dut (
        .clk        (clk),
        .rst        (rst),
        .clksel     (1'b0),      // external clock mode
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

    // Answer key: first 10 Fibonacci numbers
    reg [15:0] fib [0:9];
    initial begin
        fib[0]=16'd1;  fib[1]=16'd1;  fib[2]=16'd2;  fib[3]=16'd3;  fib[4]=16'd5;
        fib[5]=16'd8;  fib[6]=16'd13; fib[7]=16'd21; fib[8]=16'd34; fib[9]=16'd55;
    end

    // GPIO watchdog
    integer writes;
    integer errors;
    integer k;

    wire gpio_write_now = dut.gpio_wr_sel;
    wire [15:0] gpio_write_value = dut.bus_wdata;

    always @(posedge clk) begin
        if (gpio_write_now) begin
            writes = writes + 1;
            if (writes <= 10) begin
                if (gpio_write_value !== fib[writes-1]) begin
                    errors = errors + 1;
                    $display("  [FAIL] GPIO write #%0d = 0x%04h  (expected 0x%04h)",
                             writes, gpio_write_value, fib[writes-1]);
                end else begin
                    $display("  [ OK ] GPIO write #%0d = 0x%04h  (Fibonacci #%0d)",
                             writes, gpio_write_value, writes);
                end
            end
        end
    end

    initial begin
        $dumpfile("build/tb_t16_soc.vcd");
        $dumpvars(0, tb_t16_soc);

        writes = 0;
        errors = 0;
        gpio_in = 16'h0000;

        $display("");
        $display("=====================================================");
        $display("  T-16 V4.1  |  TEST 1: Fibonacci on GPIO");
        $display("  Simulator: Icarus Verilog");
        $display("=====================================================");
        $display("  Program prints the first 10 Fibonacci numbers");
        $display("  onto the 16 output pins, then halts.");
        $display("");

        rst = 1'b1;
        repeat (2) @(posedge clk);
        rst = 1'b0;
        $display("  Reset released - the CPU is running its program...");

        k = 0;
        while (!halted && k < 10000) begin
            @(posedge clk);
            k = k + 1;
        end
        #1;

        $display("");
        if (halted !== 1'b1) begin
            $display("  [FAIL] CPU never reached HALT (timeout after %0d cycles)", k);
            errors = errors + 1;
        end else begin
            $display("  [ OK ] CPU reached HALT after %0d clock cycles.", k);
        end

        if (writes !== 10) begin
            $display("  [FAIL] GPIO was written %0d times (expected exactly 10).", writes);
            errors = errors + 1;
        end else begin
            $display("  [ OK ] GPIO was written exactly 10 times.");
        end

        if (errors == 0) begin
            $display("");
            $display("  ==============================================");
            $display("   *** TEST 1 PASSED - T-16 COMPUTES CORRECTLY ***");
            $display("  ==============================================");
        end else begin
            $display("");
            $display("  **********************************************");
            $display("   *** TEST 1 FAILED - %0d error(s) ***", errors);
            $display("  **********************************************");
        end
        $display("");
        $finish;
    end

endmodule
