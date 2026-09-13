// ============================================================================
//  T-16 SOC  ("the whole chip")  —  V4 TOP LEVEL
//  File    : rtl/t16_soc.v
//
//  This is the HEART of V4: it wires V3's clean single-cycle CPU together
//  with V2's ring oscillator, TIMER, SENSOR, and P-bit — all accessible
//  as memory-mapped peripherals. The CPU ISA is UNCHANGED from V3.
//
//  THE V4 ARCHITECTURE:
//
//        +----------------------------------------------------------+
//  clk --|-->  [Clock Mux] -+-> t16_cpu <-> t16_rom (program)       |
//  rst --|                  |      |                                 |
//        |   [Ring Osc]-----+      |<--- data bus --->               |
//        |   [Prescaler]           |                                 |
//        |                    +----+----+----+----+----+----+        |
//        |                    |    |    |    |    |    |    |        |
//  io ---|                   RAM  GPIO GPIO TIMER SENSR MSR  WAIT   |
//  out<--|                   R/W  OUT   IN  (RO)  (RO) P-bit sleep  |
//        +----------------------------------------------------------+
//
//  THE ADDRESS MAP (memory-mapped peripherals):
//    0x0000 - 0x007F : RAM      (128 words, read/write)
//    0x0080          : GPIO OUT (write = set pins, read = see them)
//    0x0081          : GPIO IN  (read the input pins)
//    0x0082          : TIMER    (read-only, 16-bit free-running counter)
//    0x0083          : SENSOR   (read-only, counts ring oscillator pulses)
//    0x0084          : MSR/P-bit(read = get P-bit, write = set P-bit[0])
//    0x0085          : WAIT     (write = sleep until heartbeat if P=0)
//    anything else   : black hole (writes dropped, reads return 0)
//
//  CLOCK MODES (controlled by clksel input):
//    clksel=0 : CPU clock = external clk pin (normal demo mode)
//    clksel=1 : CPU clock = RO/32 (self-clocked, no external clock needed)
//               This is the key to the ultra-low-VDD record experiment.
//
//  Project : TELUGU T-16 V4.1 | License : Apache-2.0
// ============================================================================

`timescale 1ns / 1ps

module t16_soc #(
    parameter ROM_DEPTH    = 256,
    parameter RAM_DEPTH    = 128,
    parameter INIT_FILE    = "",
    parameter integer USE_RO     = 0,       // 0=sim/FPGA, 1=silicon (sky130 ring)
    parameter integer SENSOR_TAP = 2        // RO prescaler bit for SENSOR (2=sim, 7=silicon)
) (
    input  wire        clk,        // external chip clock
    input  wire        rst,        // chip reset (1 = restart, active HIGH for V4)
    input  wire        clksel,     // 0=external clock, 1=self-clock from ring osc
    input  wire [15:0] gpio_in,    // 16 input pins
    output wire [15:0] gpio_out,   // 16 output pins
    output wire        halted,     // 1 = the program reached HALT
    output wire        sleeping,   // 1 = CPU is in WAIT sleep mode

    // Ring oscillator / measurement pins
    input  wire        ro_sim_clk, // deterministic RO for simulation (USE_RO=0)
    output wire        ro_out_pin, // raw ring oscillator output (scope tap)
    output wire        msr_p_pin   // live P-bit status (scope tap)
);

    // ======================================================================
    // 1. RING OSCILLATOR + PRESCALER
    // ======================================================================
    wire ro_out_raw;

    t16_ro #(
        .USE_RO(USE_RO)
    ) u_ro (
        .ena       (1'b1),
        .ro_sim_clk(ro_sim_clk),
        .ro_out    (ro_out_raw)
    );

    assign ro_out_pin = ro_out_raw;

    // 8-bit prescaler clocked by the ring oscillator
    // ro_cnt[4] = RO/32  -> CPU clock in self-clocked mode
    // ro_cnt[SENSOR_TAP] -> the sensor tap
    //
    // V4.1 CRITICAL FIX: this counter has NO reset on purpose. It must
    // keep counting even while rst=1, because in self-clocked mode the
    // CPU clock IS ro_cnt[4] - if reset froze this counter, the CPU
    // clock would stop, and the CPU could never take the clock edges it
    // needs to clear its own halt flag. The chip would boot dead.
    // (A free-running divider does not care about its start value:
    // simulation starts it at 0 for determinism; silicon powers up at
    // a random value, which only shifts the phase - harmless.)
    reg [7:0] ro_cnt = 8'd0;
    always @(posedge ro_out_raw)
        ro_cnt <= ro_cnt + 8'd1;

    // ======================================================================
    // 2. CPU CLOCK SELECT (STATIC — do not switch while running!)
    // ======================================================================
    wire cpu_clk = clksel ? ro_cnt[4] : clk;

    // ======================================================================
    // 3. TIMER — 16-bit free-running counter (CPU clock domain)
    //    Runs even while CPU is in WAIT sleep. TIMER[15] = heartbeat
    //    that wakes the CPU from WAIT (one tick every 32768 cycles).
    // ======================================================================
    reg [15:0] timer;
    always @(posedge cpu_clk or posedge rst) begin
        if (rst)
            timer <= 16'd0;
        else
            timer <= timer + 16'd1;
    end

    // ======================================================================
    // 4. SENSOR — counts ring oscillator prescaler edges
    //    This is the temperature / supply-voltage proxy.
    //    In sub-threshold, higher temperature = higher frequency = faster
    //    SENSOR increment. Software reads this and decides eco vs turbo.
    // ======================================================================
    reg [15:0] sensor;
    reg [1:0]  tap_sync;     // 2-FF synchronizer for cross-domain tap
    reg        tap_d;        // edge detect

    always @(posedge cpu_clk or posedge rst) begin
        if (rst) begin
            sensor   <= 16'd0;
            tap_sync <= 2'b00;
            tap_d    <= 1'b0;
        end else begin
            tap_sync <= {tap_sync[0], ro_cnt[SENSOR_TAP]};
            tap_d    <= tap_sync[1];
            if (tap_sync[1] & ~tap_d)    // rising edge of the tap
                sensor <= sensor + 16'd1;
        end
    end

    // ======================================================================
    // 5. P-BIT (MSR) — THE owner's thermal-adaptive idea
    //    P=0: eco mode (WAIT instruction sleeps until heartbeat)
    //    P=1: turbo mode (WAIT is ignored, CPU races through)
    //    Software reads SENSOR, compares to threshold, sets P accordingly.
    // ======================================================================
    reg msr_p;
    assign msr_p_pin = msr_p;

    // ======================================================================
    // 6. WAIT / SLEEP LOGIC
    //    When CPU writes to address 0x0085 AND P=0 AND no heartbeat edge:
    //    freeze the CPU clock enable until the next TIMER[15] rising edge.
    // ======================================================================
    reg  sleep_r;             // 1 = CPU is asleep
    reg  timer15_d;           // previous TIMER[15] for edge detect
    wire timer15_rise = timer[15] & ~timer15_d;

    always @(posedge cpu_clk or posedge rst) begin
        if (rst) begin
            sleep_r   <= 1'b0;
            timer15_d <= 1'b0;
        end else begin
            timer15_d <= timer[15];
            if (sleep_r) begin
                // Wake up on heartbeat
                if (timer15_rise)
                    sleep_r <= 1'b0;
            end else begin
                // Enter sleep: writing to WAIT register when P=0
                if (wait_trigger && !msr_p && !timer15_rise)
                    sleep_r <= 1'b1;
            end
        end
    end

    assign sleeping = sleep_r;

    // CPU enable: frozen during sleep
    wire cpu_ena = !sleep_r;

    // ======================================================================
    // 7. THE CPU — and its bus wires
    // ======================================================================
    wire [15:0] cpu_pc;
    wire [15:0] cpu_instr;
    wire [15:0] bus_addr;
    wire [15:0] bus_wdata;
    wire        bus_we;
    wire [15:0] bus_rdata;
    wire        cpu_halt;

    // Gate the CPU clock with sleep
    // (In a real design you'd use a clock gate cell; for simulation,
    //  we use the enable approach — halt+sleep both stop state changes.)
    reg cpu_clk_gated_en;
    always @(negedge cpu_clk or posedge rst) begin
        if (rst)
            cpu_clk_gated_en <= 1'b1;
        else
            cpu_clk_gated_en <= cpu_ena;
    end
    wire cpu_clk_g = cpu_clk & cpu_clk_gated_en;

    t16_cpu u_cpu (
        .clk      (cpu_clk_g),
        .rst      (rst),
        .pc       (cpu_pc),
        .instr    (cpu_instr),
        .mem_addr (bus_addr),
        .mem_dout (bus_wdata),
        .mem_we   (bus_we),
        .mem_din  (bus_rdata),
        .halt     (cpu_halt)
    );

    // ======================================================================
    // 8. PROGRAM ROM
    // ======================================================================
    t16_rom #(
        .ROM_DEPTH(ROM_DEPTH),
        .INIT_FILE(INIT_FILE)
    ) u_rom (
        .addr  (cpu_pc),
        .instr (cpu_instr)
    );

    // ======================================================================
    // 9. ADDRESS DECODING — which peripheral gets the bus transaction?
    // ======================================================================
    wire ram_sel      = (bus_addr[15:7] == 9'b000000000);    // 0x0000..0x007F
    wire gpio_wr_sel  = (bus_addr == 16'h0080) &&  bus_we;   // writing GPIO out
    wire gpio_rd_sel  = (bus_addr == 16'h0080);               // reading GPIO out
    wire gpio_in_sel  = (bus_addr == 16'h0081);               // reading GPIO in
    wire timer_sel    = (bus_addr == 16'h0082);               // reading TIMER
    wire sensor_sel   = (bus_addr == 16'h0083);               // reading SENSOR
    wire msr_rd_sel   = (bus_addr == 16'h0084);               // reading P-bit
    wire msr_wr_sel   = (bus_addr == 16'h0084) &&  bus_we;   // writing P-bit
    wire wait_trigger = (bus_addr == 16'h0085) &&  bus_we;   // triggering WAIT

    // ======================================================================
    // 10. RAM
    // ======================================================================
    wire [15:0] ram_dout;

    t16_ram #(
        .RAM_DEPTH(RAM_DEPTH)
    ) u_ram (
        .clk  (cpu_clk_g),
        .we   (bus_we && ram_sel),
        .addr (bus_addr[$clog2(RAM_DEPTH)-1:0]),
        .din  (bus_wdata),
        .dout (ram_dout)
    );

    // ======================================================================
    // 11. GPIO
    // ======================================================================
    wire [15:0] gpio_rdback;

    t16_gpio u_gpio (
        .clk      (cpu_clk_g),
        .we       (gpio_wr_sel),
        .din      (bus_wdata),
        .dout     (gpio_rdback),
        .pins_out (gpio_out)
    );

    // ======================================================================
    // 12. P-BIT WRITE
    // ======================================================================
    always @(posedge cpu_clk_g or posedge rst) begin
        if (rst)
            msr_p <= 1'b0;
        else if (msr_wr_sel)
            msr_p <= bus_wdata[0];
    end

    // ======================================================================
    // 13. READ MUX — which peripheral answers the CPU's read?
    // ======================================================================
    assign bus_rdata = ram_sel     ? ram_dout      :
                       gpio_rd_sel ? gpio_rdback   :
                       gpio_in_sel ? gpio_in       :
                       timer_sel   ? timer         :
                       sensor_sel  ? sensor        :
                       msr_rd_sel  ? {15'b0, msr_p}:
                                     16'h0000;

    assign halted = cpu_halt;

endmodule
