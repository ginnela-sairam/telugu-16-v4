// ============================================================================
//  T-16 CPU CORE  ("the brain")  —  V4
//  File    : rtl/t16_cpu.v
//  What it is: a 16-bit single-cycle microprocessor.
//              8 registers, 14 instructions, runs at any clock speed.
//
//  THIS FILE IS IDENTICAL TO THE V3 PROVEN CORE.
//  P-bit, TIMER, SENSOR are memory-mapped peripherals in t16_soc.v,
//  so this CPU needs zero modifications — the ISA stays verified.
//
//  INSTRUCTION FORMAT (one instruction = one 16-bit word):
//
//     Register form:  [15:12]=opcode [11:9]=Rd [8:6]=Ra [5:3]=Rb [2:0]=func
//     Immediate form: [15:12]=opcode [11:9]=Rd [8:0]........=imm9 (9-bit value)
//
//     Example:  ADD R3, R1, R2  means  R3 = R1 + R2
//              LDI R1, 100      means  R1 = 100
//
//  Project : TELUGU T-16 V4.1
//  License : Apache-2.0
// ============================================================================

`timescale 1ns / 1ps

module t16_cpu (
    // ---- clock and reset -------------------------------------------------
    input  wire        clk,      // the heartbeat; everything advances on rising edge
    input  wire        rst,      // 1 = reset the CPU (program restarts at address 0)

    // ---- instruction memory (program) interface --------------------------
    output wire [15:0] pc,       // Program Counter = address of current instruction
    input  wire [15:0] instr,    // the 16-bit instruction ROM gives back for that address

    // ---- data memory (RAM / GPIO) interface ------------------------------
    output wire [15:0] mem_addr, // address to read/write (only used by LDM/STM)
    output wire [15:0] mem_dout, // data being WRITTEN out (only used by STM)
    output wire        mem_we,   // 1 = we are writing to memory this cycle (STM)
    input  wire [15:0] mem_din,  // data being READ in (only used by LDM)

    // ---- status ----------------------------------------------------------
    output reg         halt      // 1 = CPU executed HALT and froze itself
);

    // ========================================================================
    // 1. OPCODES - the 16 possible "verbs" of the machine
    // ========================================================================
    localparam OP_ADD  = 4'h0;   // Rd = Ra + Rb
    localparam OP_SUB  = 4'h1;   // Rd = Ra - Rb
    localparam OP_AND  = 4'h2;   // Rd = Ra & Rb   (bitwise)
    localparam OP_OR   = 4'h3;   // Rd = Ra | Rb   (bitwise)
    localparam OP_XOR  = 4'h4;   // Rd = Ra ^ Rb   (bitwise)
    localparam OP_SH   = 4'h5;   // Rd = Ra shifted by Rb (func picks how)
    localparam OP_LDI  = 4'h6;   // Rd = imm9      (put a constant in a register)
    localparam OP_LDM  = 4'h7;   // Rd = MEM[Ra+Rb] (load from memory)
    localparam OP_STM  = 4'h8;   // MEM[Ra+Rb] = Rd (store to memory)
    localparam OP_BEQZ = 4'hA;   // if Rd==0, jump  (branch if zero)
    localparam OP_BNEZ = 4'hB;   // if Rd!=0, jump  (branch if not zero)
    localparam OP_JAL  = 4'hC;   // call: Rd=return address, PC jumps
    localparam OP_JR   = 4'hD;   // return: PC = Rd
    localparam OP_HALT = 4'hF;   // stop the CPU forever

    // ========================================================================
    // 2. DECODE - slice the 16-bit instruction into its fields
    // ========================================================================
    wire [3:0]  opcode = instr[15:12];  // the "verb"
    wire [2:0]  rd     = instr[11:9];   // destination register number (0-7)
    wire [2:0]  ra     = instr[8:6];    // first source register number
    wire [2:0]  rb     = instr[5:3];    // second source register number
    wire [2:0]  func   = instr[2:0];    // sub-function (used only by shifts)

    // 9-bit immediate, treated as SIGNED so it can hold -256 .. +255.
    wire signed [8:0] imm9    = instr[8:0];
    wire [15:0]        imm_sext = {{7{imm9[8]}}, imm9};

    // ========================================================================
    // 3. REGISTERS - eight 16-bit drawers to keep numbers in
    // ========================================================================
    reg [15:0] regs [0:7];

    wire [15:0] ra_val = regs[ra];
    wire [15:0] rb_val = regs[rb];
    wire [15:0] rd_val = regs[rd];

    // ========================================================================
    // 4. ALU - the calculator
    // ========================================================================
    reg [15:0] alu_result;

    always @* begin
        alu_result = 16'h0000;
        case (opcode)
            OP_ADD:  alu_result = ra_val + rb_val;
            OP_SUB:  alu_result = ra_val - rb_val;
            OP_AND:  alu_result = ra_val & rb_val;
            OP_OR :  alu_result = ra_val | rb_val;
            OP_XOR:  alu_result = ra_val ^ rb_val;
            OP_SH: begin
                case (func)
                    3'd0:    alu_result = ra_val << rb_val[3:0];
                    3'd1:    alu_result = ra_val >> rb_val[3:0];
                    default: alu_result = $signed(ra_val) >>> rb_val[3:0];
                endcase
            end
            OP_LDI:  alu_result = imm_sext;
            OP_LDM,
            OP_STM:  alu_result = ra_val + rb_val;
            default: alu_result = 16'h0000;
        endcase
    end

    // ========================================================================
    // 5. MEMORY INTERFACE SIGNALS
    // ========================================================================
    assign mem_addr = alu_result;
    assign mem_dout = rd_val;
    assign mem_we   = (opcode == OP_STM) && !halt;

    // ========================================================================
    // 6. NEXT-PC LOGIC
    // ========================================================================
    reg [15:0] pc_r;
    assign pc = pc_r;

    reg [15:0] pc_next;
    always @* begin
        pc_next = pc_r + 16'd1;
        if (!halt) begin
            case (opcode)
                OP_BEQZ: if (rd_val == 16'h0000)
                             pc_next = pc_r + 16'd1 + imm_sext;
                OP_BNEZ: if (rd_val != 16'h0000)
                             pc_next = pc_r + 16'd1 + imm_sext;
                OP_JAL : pc_next = pc_r + 16'd1 + imm_sext;
                OP_JR  : pc_next = rd_val;
                OP_HALT: pc_next = pc_r;
                default: ;
            endcase
        end else begin
            pc_next = pc_r;
        end
    end

    // ========================================================================
    // 7. THE HEARTBEAT — on every rising clock edge commit state
    // ========================================================================
    integer i;
    always @(posedge clk) begin
        if (rst) begin
            pc_r <= 16'h0000;
            halt <= 1'b0;
            for (i = 0; i < 8; i = i + 1)
                regs[i] <= 16'h0000;
        end else if (!halt) begin
            pc_r <= pc_next;
            case (opcode)
                OP_ADD, OP_SUB, OP_AND, OP_OR, OP_XOR, OP_SH, OP_LDI:
                    regs[rd] <= alu_result;
                OP_LDM: regs[rd] <= mem_din;
                OP_JAL: regs[rd] <= pc_r + 16'd1;
                default: ;
            endcase
            if (opcode == OP_HALT)
                halt <= 1'b1;
        end
    end

endmodule
