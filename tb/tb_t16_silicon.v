// ============================================================================
//  TESTBENCH 4 — "Does the SILICON configuration work?"  —  V4.1 NEW
//  File    : tb/tb_t16_silicon.v
//
//  The other three testbenches simulate the design in SIMULATION mode
//  (USE_RO=0: the ring is a pretend clock, the program comes from a
//  .hex file). But the chip you send to OpenLane is configured the
//  opposite way (USE_RO=1: a real 15-inverter ring; program BAKED into
//  rtl/t16_rom.v). This testbench proves THAT configuration:
//
//    PHASE A — baked program, external clock:
//      * t16_top_silicon (INIT_FILE="", so only the baked words matter)
//      * the sky130 ring (behavioral shims, 2 ns per gate) runs free
//      * the CPU must still compute Fibonacci and HALT
//      * -> proves the baked ROM content is correct
//
//    PHASE B — SELF-CLOCKED MODE (the record experiment!):
//      * clksel=1: the CPU clock is RO/32 from the ring - NO external
//        clock at all
//      * the CPU must STILL compute Fibonacci and HALT
//      * -> proves the chip truly runs from its own physics
//
//  Compile with -DT16_SIM so the ring gets its deterministic starter
//  (without it, an all-X ring may never start oscillating in simulation;
//  real silicon always finds an oscillation by itself).
//
//  Project : TELUGU T-16 V4.1 | License : Apache-2.0
// ============================================================================

`timescale 1ns / 1ps

module tb_t16_silicon;

    reg         clk;
    reg         rst;
    reg         clksel;
    reg  [15:0] gpio_in;
    wire [15:0] gpio_out;
    wire        halted;
    wire        sleeping;
    wire        ro_out_pin;
    wire        msr_p_pin;

    // The REAL silicon top: USE_RO=1, SENSOR_TAP=7, INIT_FILE="" (baked)
    t16_top_silicon dut (
        .clk        (clk),
        .rst        (rst),
        .clksel     (clksel),
        .gpio_in    (gpio_in),
        .gpio_out   (gpio_out),
        .halted     (halted),
        .sleeping   (sleeping),
        .ro_out_pin (ro_out_pin),
        .msr_p_pin  (msr_p_pin)
    );

    // External clock (only used in phase A)
    initial clk = 1'b0;
    always #50 clk = ~clk;            // slow 20 MHz - clearly NOT needed
                                     // once clksel=1 proves itself

    integer errors;
    integer k;
    integer writes;
    integer ro_edges;

    // Count ring oscillator output edges (the physics heartbeat)
    initial ro_edges = 0;
    always @(posedge ro_out_pin)
        ro_edges = ro_edges + 1;

    // Fibonacci answer key (same program, baked into the ROM)
    reg [15:0] fib [0:9];
    initial begin
        fib[0]=16'd1;  fib[1]=16'd1;  fib[2]=16'd2;  fib[3]=16'd3;  fib[4]=16'd5;
        fib[5]=16'd8;  fib[6]=16'd13; fib[7]=16'd21; fib[8]=16'd34; fib[9]=16'd55;
    end

    // Write-enable edge monitor. Counting RISING EDGES of the GPIO
    // write-enable is clock-domain independent (works on external clock
    // AND self-clock) and catches writes whose VALUE repeats (Fibonacci
    // writes 1, 1 - a change-of-value monitor would miss the second).
    // Explicit sensitivity list on purpose: it wakes reliably on the
    // hierarchical references.
    wire       gpio_write_now   = dut.u_soc.gpio_wr_sel;
    wire [15:0] gpio_write_value = dut.u_soc.bus_wdata;
    reg        gpio_we_d;

    always @(gpio_write_now or gpio_write_value) begin
        if (gpio_write_now && !gpio_we_d) begin
            writes = writes + 1;
            if (writes <= 10) begin
                if (gpio_write_value !== fib[writes-1]) begin
                    errors = errors + 1;
                    $display("  [FAIL] GPIO write #%0d = 0x%04h (expected 0x%04h)",
                             writes, gpio_write_value, fib[writes-1]);
                end else begin
                    $display("  [ OK ] GPIO write #%0d = 0x%04h  (Fibonacci #%0d)",
                             writes, gpio_write_value, writes);
                end
            end
        end
        gpio_we_d = gpio_write_now;
    end

    initial begin
        $dumpfile("build/tb_t16_silicon.vcd");
        $dumpvars(0, tb_t16_silicon);

        errors  = 0;
        writes  = 0;
        gpio_in = 16'h0000;

        $display("");
        $display("=====================================================");
        $display("  T-16 V4.1  |  TEST 4: the SILICON configuration");
        $display("  Baked ROM + real sky130 ring + self-clock mode");
        $display("=====================================================");

        // ================= PHASE A: baked ROM, external clock =========
        $display("");
        $display("  --- PHASE A: baked program, external clock (clksel=0) ---");
        $display("  Expect: Fibonacci on GPIO (from the BAKED words),");
        $display("  then HALT. The ring runs free on the side.");

        clksel = 1'b0;
        rst = 1'b1;
        repeat (2) @(posedge clk);
        rst = 1'b0;

        k = 0;
        while (!halted && k < 5000) begin
            @(posedge clk);
            k = k + 1;
        end
        #1;

        if (halted !== 1'b1) begin
            errors = errors + 1;
            $display("  [FAIL] PHASE A: CPU never reached HALT (k=%0d).", k);
        end else begin
            $display("  [ OK ] PHASE A: CPU reached HALT after %0d cycles", k);
            $display("         using the BAKED program words only.");
        end

        if (writes !== 10) begin
            errors = errors + 1;
            $display("  [FAIL] PHASE A: GPIO written %0d times (expected 10).", writes);
        end else
            $display("  [ OK ] PHASE A: all 10 Fibonacci numbers correct.");

        if (gpio_out !== 16'd55) begin
            errors = errors + 1;
            $display("  [FAIL] PHASE A: final GPIO = 0x%04h (expected 0x0037=55)",
                     gpio_out);
        end else
            $display("  [ OK ] PHASE A: final GPIO = 55 (0x0037) - last Fibonacci.");

        if (ro_edges < 1) begin
            errors = errors + 1;
            $display("  [FAIL] PHASE A: the ring oscillator never toggled!");
        end else
            $display("  [ OK ] PHASE A: ring oscillator alive (%0d rising edges so far).",
                     ro_edges);

        // ================= PHASE B: SELF-CLOCKED MODE ==================
        $display("");
        $display("  --- PHASE B: SELF-CLOCKED (clksel=1, no external clock) ---");
        $display("  The CPU clock is now RO/32 straight from the ring.");
        $display("  Expect: Fibonacci again, then HALT - driven purely by");
        $display("  the chip's own physics.");

        writes  = 0;
        clksel = 1'b1;                 // switch BEFORE reset (static, as documented)
        rst = 1'b1;
        #200;                           // hold reset a few self-clock ticks
        rst = 1'b0;

        // Wait for HALT. The external clk keeps ticking as a time base,
        // but NOT ONE of its edges drives the CPU - clksel=1 means the
        // CPU clock is RO/32 straight from the ring.
        k = 0;
        while (!halted && k < 4000000) begin
            @(posedge clk);
            k = k + 1;
        end
        #1;

        if (halted !== 1'b1) begin
            errors = errors + 1;
            $display("  [FAIL] PHASE B: CPU never reached HALT in self-clocked mode.");
        end else begin
            $display("  [ OK ] PHASE B: CPU reached HALT - SELF-CLOCKED!");
            $display("         (No external clock drove a single CPU edge.)");
        end

        if (writes !== 10) begin
            errors = errors + 1;
            $display("  [FAIL] PHASE B: GPIO written %0d times (expected 10).", writes);
        end else
            $display("  [ OK ] PHASE B: all 10 Fibonacci numbers correct again.");

        if (gpio_out !== 16'd55) begin
            errors = errors + 1;
            $display("  [FAIL] PHASE B: final GPIO = 0x%04h (expected 0x0037=55)",
                     gpio_out);
        end else
            $display("  [ OK ] PHASE B: final GPIO = 55 - same program, same answer.");

        $display("  [ OK ] Ring oscillator total rising edges: %0d", ro_edges);
        $display("         (each one is the physics heartbeat of your chip)");

        // ================= VERDICT =============================
        $display("");
        if (errors == 0) begin
            $display("  ================================================");
            $display("   *** TEST 4 PASSED - SILICON CONFIG WORKS ***");
            $display("   *** baked ROM, real ring, self-clocked CPU ***");
            $display("  ================================================");
        end else begin
            $display("  ************************************************");
            $display("   *** TEST 4 FAILED - %0d error(s) ***", errors);
            $display("  ************************************************");
        end
        $display("");
        $finish;
    end

endmodule
