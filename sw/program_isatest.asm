; ============================================================================
;  program_isatest.asm  -  THE FULL INSTRUCTION TEST PROGRAM
; ----------------------------------------------------------------------------
;  WHAT IT DOES: uses EVERY instruction at least once and stores each result
;                in RAM as a "signature". The testbench (tb/tb_t16_isa.v)
;                checks the signature at HALT - if any instruction is broken,
;                its word in RAM will be wrong.
;
;  RAM at HALT (the signature the testbench expects):
;     RAM[0]  = 0x0011   ADD   10 + 7
;     RAM[1]  = 0x000A   SUB   17 - 7
;     RAM[2]  = 0x0008   AND   12 & 10
;     RAM[3]  = 0x000E   OR    12 | 10
;     RAM[4]  = 0x0006   XOR   12 ^ 10
;     RAM[5]  = 0x000C   SLL   3 << 2
;     RAM[6]  = 0x0FF0   SRL   0xFF00 >> 4 (logical: zeros come in)
;     RAM[7]  = 0xFFF0   SRA   0xFF00 >> 4 (arithmetic: sign comes in)
;     RAM[8]  = 0x0011   LDM   reading RAM[0] back
;     RAM[9]  = 0xA5A5   LDM   reading the GPIO input pins
;     RAM[10] = 0x0077   JAL+JR the subroutine ran and returned
;     GPIO    = 0x600D   the "GOOD" magic value (built with shifts + OR)
; ============================================================================

        LDI   R6, 0          ; R6 = constant ZERO
        LDI   R7, 1          ; R7 = constant ONE
        LDI   R0, 0          ; R0 = where we are in RAM (write index)

; ---- arithmetic: 10 + 7 = 17, then 17 - 7 = 10 ---------------------------
        LDI   R1, 10
        LDI   R2, 7
        ADD   R3, R1, R2     ; 17
        STM   R3, [R6+R0]    ; RAM[0] = 17
        ADD   R0, R0, R7     ; index++
        SUB   R4, R3, R2     ; 10
        STM   R4, [R6+R0]    ; RAM[1] = 10
        ADD   R0, R0, R7     ; index++

; ---- logic: 12 and 10 -----------------------------------------------------
        LDI   R1, 12         ; 12 = binary 1100
        LDI   R2, 10         ; 10 = binary 1010
        AND   R3, R1, R2     ;  8 = binary 1000
        STM   R3, [R6+R0]    ; RAM[2] = 8
        ADD   R0, R0, R7
        OR    R4, R1, R2     ; 14 = binary 1110
        STM   R4, [R6+R0]    ; RAM[3] = 14
        ADD   R0, R0, R7
        XOR   R5, R1, R2     ;  6 = binary 0110
        STM   R5, [R6+R0]    ; RAM[4] = 6
        ADD   R0, R0, R7

; ---- shifts ----------------------------------------------------------------
        LDI   R1, 3
        LDI   R2, 2
        SLL   R3, R1, R2     ; 3 << 2 = 12
        STM   R3, [R6+R0]    ; RAM[5] = 12
        ADD   R0, R0, R7

        LDI   R1, -256       ; -256 = 0xFF00 (16 bits, sign on top)
        LDI   R2, 4
        SRL   R3, R1, R2     ; 0x0FF0 (logical right: zeros fill in)
        STM   R3, [R6+R0]    ; RAM[6] = 0x0FF0
        ADD   R0, R0, R7
        SRA   R3, R1, R2     ; 0xFFF0 (arithmetic right: sign fills in)
        STM   R3, [R6+R0]    ; RAM[7] = 0xFFF0
        ADD   R0, R0, R7

; ---- memory: write then read back ------------------------------------------
        LDM   R4, R6, R6     ; R4 = memory[R6+R6] = RAM[0] = 17
        STM   R4, [R6+R0]    ; RAM[8] = 17 (proof the load worked)
        ADD   R0, R0, R7

        LDI   R4, 0x81       ; 0x81 = GPIO input pins
        LDM   R2, R4, R6     ; R2 = the input pin value (testbench drives 0xA5A5)
        STM   R2, [R6+R0]    ; RAM[9] = 0xA5A5
        ADD   R0, R0, R7

; ---- branches: taken and not-taken, plus trap lines ------------------------
;  Each POISON line would write garbage into the signature if a branch
;  failed to jump over it. Correct behavior = they never execute.
        LDI   R1, 0
        BEQZ  R1, over1      ; R1 == 0 -> MUST jump (branch taken)
        STM   R7, [R6+R0]    ; POISON 1 - must be skipped
over1:  BNEZ  R7, over2      ; R7 == 1 -> MUST jump
        STM   R7, [R6+R0]    ; POISON 2 - must be skipped
over2:

; ---- subroutine call and return ---------------------------------------------
        JAL   R5, my_sub     ; call the subroutine; R5 = return address
        STM   R2, [R6+R0]    ; RAM[10] = 0x77 (only right if the sub returned)
        ADD   R0, R0, R7
        BEQZ  R6, done       ; R6 == 0 always -> jump OVER the subroutine
        STM   R7, [R6+R0]    ; POISON 3 - never executes

my_sub: LDI   R2, 0x77       ; subroutine body: R2 = 0x77
        JR    R5             ; return to the instruction after the JAL

; ---- build 0x600D ("GOOD") and show it on the pins --------------------------
done:   LDI   R1, 0x60
        LDI   R2, 8
        SLL   R1, R1, R2     ; 0x60 << 8 = 0x6000
        LDI   R2, 0x0D
        OR    R1, R1, R2     ; 0x6000 | 0x0D = 0x600D
        LDI   R4, 0x80
        STM   R1, [R4+R6]    ; GPIO = 0x600D

        HALT                 ; freeze - testbench now checks the signature
