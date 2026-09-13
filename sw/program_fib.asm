; ============================================================================
;  program_fib.asm  -  THE MAIN DEMO PROGRAM
; ----------------------------------------------------------------------------
;  WHAT IT DOES: computes the Fibonacci sequence and "prints" each number
;                onto the 16 GPIO output pins, then halts.
;
;                Fibonacci: 1 1 2 3 5 8 13 21 34 55 ...
;                (each number = the two before it, added together)
;
;  WHY IT MATTERS: this is the classic "first program" for a new CPU.
;                If your chip can do this, arithmetic, memory, branches,
;                loops and I/O all work. It is the whole machine in 14 lines.
;
;  AFTER EDITING: rebuild the .hex with:
;                python3 tools/t16asm.py sw/program_fib.asm sw/program_fib.hex
;                then run: bash run_sim.sh
; ============================================================================

        LDI   R4, 0x80       ; R4 = 0x0080 = address of the GPIO output pins
        LDI   R0, 0          ; R0 = 0 (offset used for addressing: [R4+R0])
        LDI   R1, 0          ; R1 = a (the older Fibonacci number)   = 0
        LDI   R2, 1          ; R2 = b (the newer Fibonacci number)   = 1
        LDI   R3, 10         ; R3 = how many numbers we will print   = 10
        LDI   R6, 0          ; R6 = constant ZERO  (a software trick:
                             ;      OR Rx, Ry, R6 copies Ry into Rx)
        LDI   R7, 1          ; R7 = constant ONE   (used for counting down)

loop:   STM   R2, [R4+R0]   ; *** show b on the GPIO pins (16 LEDs) ***
        ADD   R5, R1, R2    ; R5 = a + b        (the next number)
        OR    R1, R2, R6    ; a = b             (copy via OR with zero)
        OR    R2, R5, R6    ; b = R5            (b becomes the new number)
        SUB   R3, R3, R7    ; count = count - 1 (one less to go)
        BNEZ  R3, loop      ; if count is not zero, jump back to 'loop'

        HALT                 ; done - freeze the CPU (the 'halted' LED lights)
