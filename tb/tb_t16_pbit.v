// ============================================================================
//  TESTBENCH 3 — "Does the P-bit thermal-adaptive system work?"
//  File    : tb/tb_t16_pbit.v   (V4.1 — two-phase, decision-correct)
//
//  V4.1 NOTE: this testbench was upgraded because the original only
//  checked "GPIO is non-zero". It now PROVES the actual behavior:
//
//    PHASE 1 — COOL CHIP (slow ring, sensor < threshold):
//      * the program must choose ECO mode  (P=0)
//      * writing the WAIT register must put the CPU TO SLEEP
//      * the CPU must WAKE on the TIMER[15] heartbeat
//      * final GPIO = 0xEC01 (eco marker + the wake-up receipt)
//
//    PHASE 2 — HOT CHIP (fast ring, sensor >= threshold):
//      * the program must choose TURBO mode (P=1)
//      * the WAIT write is IGNORED (no sleep at all)
//      * final GPIO = 0x700C (turbo marker + raced-on receipt)
//
//  Same ROM, same CPU — only the ring oscillator speed (i.e. the
//  temperature proxy) changed. That is the whole P-bit idea in one test.
//
//  Project : TELUGU T-16 V4.1 | License : Apache-2.0
// ============================================================================

`timescale 1ns / 1ps

module tb_t16_pbit;

    reg         clk;
    reg         rst;
    reg  [15:0] gpio_in;
    wire [15:0] gpio_out;
    wire        halted;
    wire        sleeping;
    wire        ro_out_pin;
    wire        msr_p_pin;

    // Deterministic ring oscillator stand-in. Its speed is the
    // temperature proxy: slow = cool chip, fast = hot chip.
    reg ro_sim_clk;
    initial ro_sim_clk = 1'b0;
    real ro_half;                     // half-period in ns (switchable, real
    initial ro_half = 8.0;            // so 2.5 ns is allowed)
    always #ro_half ro_sim_clk = ~ro_sim_clk;

    t16_soc #(
        .ROM_DEPTH (256),
        .RAM_DEPTH (128),
        .INIT_FILE ("sw/program_pbit.hex"),
        .USE_RO    (0),               // deterministic RO stand-in
        .SENSOR_TAP(1)                // RO/4: fast-counting tap so the hot
    ) dut (                           // phase clearly crosses the threshold
                                     // (silicon uses tap 7 = RO/256)
        .clk        (clk),
        .rst        (rst),
        .clksel     (1'b0),           // external CPU clock
        .gpio_in    (gpio_in),
        .gpio_out   (gpio_out),
        .halted     (halted),
        .sleeping   (sleeping),
        .ro_sim_clk (ro_sim_clk),
        .ro_out_pin (ro_out_pin),
        .msr_p_pin  (msr_p_pin)
    );

    initial clk = 1'b0;
    always #5 clk = ~clk;             // CPU clock = 100 MHz (10 ns period)

    integer errors;
    integer k;
    integer sleep_seen;               // did the CPU ever sleep?
    integer wake_ok;                  // did it sleep AND wake again?

    // Watch the sleep pin on every CPU clock
    always @(posedge clk) begin
        if (sleeping) begin
            sleep_seen = 1;
        end else if (sleep_seen) begin
            wake_ok = 1;              // slept before, awake now
        end
    end

    // Run one program pass; returns when halted or after 'limit' cycles
    task run_program(input integer limit);
        begin
            k = 0;
            while (!halted && k < limit) begin
                @(posedge clk);
                k = k + 1;
            end
            #1;
        end
    endtask

    initial begin
        $dumpfile("build/tb_t16_pbit.vcd");
        $dumpvars(0, tb_t16_pbit);

        errors    = 0;
        gpio_in   = 16'h0000;

        $display("");
        $display("=====================================================");
        $display("  T-16 V4.1  |  TEST 3: P-bit thermal-adaptive system");
        $display("  Tests: TIMER, SENSOR, P-bit, WAIT sleep, wake-up");
        $display("=====================================================");

        // ================= PHASE 1: COOL CHIP =================
        $display("");
        $display("  --- PHASE 1: slow ring oscillator (a COOL chip) ---");
        $display("  Expect: ECO mode (P=0), real sleep, wake on");
        $display("  heartbeat, GPIO = 0xEC01 (eco + awake receipt).");

        ro_half = 8.0;                // ring period 16 ns -> sensor stays low
        sleep_seen = 0;
        wake_ok    = 0;

        rst = 1'b1;
        repeat (2) @(posedge clk);
        rst = 1'b0;

        run_program(45000);           // heartbeat fires at cycle 32768

        if (halted !== 1'b1) begin
            errors = errors + 1;
            $display("  [FAIL] PHASE 1: CPU never reached HALT (k=%0d).", k);
        end else begin
            $display("  [ OK ] PHASE 1: CPU reached HALT after %0d cycles", k);
            $display("         (slept through most of them - that is eco mode).");
        end

        if (dut.u_ram.mem[0] === 16'h0000 || dut.u_ram.mem[0] === 16'hxxxx) begin
            errors = errors + 1;
            $display("  [FAIL] RAM[0] (TIMER snapshot) = 0x%04h (expected non-zero)",
                     dut.u_ram.mem[0]);
        end else
            $display("  [ OK ] RAM[0] (TIMER snapshot) = 0x%04h", dut.u_ram.mem[0]);

        if (dut.u_ram.mem[1] === 16'hxxxx) begin
            errors = errors + 1;
            $display("  [FAIL] RAM[1] (SENSOR snapshot) = 0x%04h (expected valid)",
                     dut.u_ram.mem[1]);
        end else
            $display("  [ OK ] RAM[1] (SENSOR snapshot) = 0x%04h  (slow ring -> cool)",
                     dut.u_ram.mem[1]);

        if (dut.u_ram.mem[2] !== 16'h0000) begin
            errors = errors + 1;
            $display("  [FAIL] RAM[2] (P-bit readback) = 0x%04h (expected 0 = eco)",
                     dut.u_ram.mem[2]);
        end else
            $display("  [ OK ] RAM[2] (P-bit readback) = 0x0000  (eco mode chosen)");

        if (!sleep_seen) begin
            errors = errors + 1;
            $display("  [FAIL] CPU never entered WAIT sleep (P=0 must sleep).");
        end else
            $display("  [ OK ] CPU entered WAIT sleep - the power saver works.");

        if (!wake_ok) begin
            errors = errors + 1;
            $display("  [FAIL] CPU slept but never woke on the heartbeat.");
        end else
            $display("  [ OK ] CPU woke on the TIMER[15] heartbeat.");

        if (gpio_out !== 16'hEC01) begin
            errors = errors + 1;
            $display("  [FAIL] GPIO = 0x%04h (expected 0xEC01 = eco + awake receipt)",
                     gpio_out);
        end else
            $display("  [ OK ] GPIO = 0xEC01  (ECO marker + the wake-up receipt)");

        // ================= PHASE 2: HOT CHIP ==================
        $display("");
        $display("  --- PHASE 2: fast ring oscillator (a HOT chip) ---");
        $display("  Expect: TURBO mode (P=1), NO sleep, GPIO = 0x700C");
        $display("  (turbo marker + raced-on receipt).");

        ro_half = 2.5;                // fast ring (5 ns period): the tap rises
        sleep_seen = 0;               // every 20 ns = exactly 2 CPU clocks,
        wake_ok    = 0;               // so the sampler sees every rise cleanly

        rst = 1'b1;
        repeat (2) @(posedge clk);
        rst = 1'b0;

        run_program(2000);            // turbo pass is quick

        if (halted !== 1'b1) begin
            errors = errors + 1;
            $display("  [FAIL] PHASE 2: CPU never reached HALT (k=%0d).", k);
        end else
            $display("  [ OK ] PHASE 2: CPU reached HALT after %0d cycles", k);

        if (dut.u_ram.mem[1] === 16'hxxxx || dut.u_ram.mem[1] < 16'd3) begin
            errors = errors + 1;
            $display("  [FAIL] RAM[1] (SENSOR snapshot) = 0x%04h (expected >= 3 = hot)",
                     dut.u_ram.mem[1]);
        end else
            $display("  [ OK ] RAM[1] (SENSOR snapshot) = 0x%04h  (fast ring -> hot)",
                     dut.u_ram.mem[1]);

        if (dut.u_ram.mem[2] !== 16'h0001) begin
            errors = errors + 1;
            $display("  [FAIL] RAM[2] (P-bit readback) = 0x%04h (expected 1 = turbo)",
                     dut.u_ram.mem[2]);
        end else
            $display("  [ OK ] RAM[2] (P-bit readback) = 0x0001  (turbo mode chosen)");

        if (sleep_seen) begin
            errors = errors + 1;
            $display("  [FAIL] CPU slept in turbo mode (P=1 must ignore WAIT).");
        end else
            $display("  [ OK ] CPU never slept - turbo ignores the WAIT request.");

        if (gpio_out !== 16'h700C) begin
            errors = errors + 1;
            $display("  [FAIL] GPIO = 0x%04h (expected 0x700C = turbo + raced receipt)",
                     gpio_out);
        end else
            $display("  [ OK ] GPIO = 0x700C  (TURB marker + the raced-on receipt)");

        // ================= VERDICT =============================
        $display("");
        if (errors == 0) begin
            $display("  ================================================");
            $display("   *** TEST 3 PASSED - P-BIT SYSTEM WORKS ***");
            $display("   *** eco sleeps, turbo races, both decide ***");
            $display("   *** correctly from the sensor reading     ***");
            $display("  ================================================");
        end else begin
            $display("");
            $display("  ************************************************");
            $display("   *** TEST 3 FAILED - %0d error(s) ***", errors);
            $display("  ************************************************");
        end
        $display("");
        $finish;
    end

endmodule
