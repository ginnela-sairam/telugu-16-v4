; ============================================================================
;  program_pbit.asm  —  THE P-BIT THERMAL-ADAPTIVE DEMO (V4.1 fixed)
; ----------------------------------------------------------------------------
;  WHAT IT DOES: demonstrates the T-16's unique thermal-adaptive system,
;  end to end:
;
;   1. Reads the TIMER  (0x0082) -> RAM[0]   (proves TIMER works)
;   2. Reads the SENSOR (0x0083) -> RAM[1]   (proves SENSOR works)
;   3. SIGNED compare: is SENSOR >= 3?
;        yes -> "hot"  -> TURBO mode: P=1 (WAIT is ignored, CPU races)
;        no  -> "cool" -> ECO   mode: P=0 (WAIT sleeps until heartbeat)
;   4. Writes the mode marker to GPIO (0xEC00 = ECO, 0x700B = TURB)
;   5. Writes the WAIT register (0x0085):
;        in ECO   mode the CPU FREEZES until TIMER[15] rises (the
;                  heartbeat, every 32768 cycles) - this is the sleep
;                  that saves power
;        in TURBO mode the write is ignored - the CPU races on
;   6. Reads the P-bit back (0x0084) -> RAM[2] (proves readback works)
;   7. Adds 1 to the GPIO marker - the "+1" only appears if the CPU
;      actually WOKE UP and kept running (0xEC01 eco-awake, 0x700C
;      turbo-raced)
;   8. HALT
;
;  THE SIGNED-COMPARE TRICK (V4.1 bug fix):
;    The old version did  SUB R5,R2,R3 / BNEZ R5,turbo  which sends
;    EVERYTHING except exactly-equal to turbo. With SENSOR=0 (a cool
;    chip!) it wrongly shouted TURBO. The T-16 has no "compare" opcode,
;    but SRA (arithmetic shift right) copies the sign bit down:
;
;        SUB  R5, R2, R3      ; R5 = SENSOR - 3  (two's complement)
;        LDI  R4, 15          ; shift by 15
;        SRA  R4, R5, R4      ; R4 = 0xFFFF if negative, 0x0000 if not
;        BNEZ R4, eco         ; negative -> SENSOR < 3 -> cool -> ECO
;
;  ADDRESS MAP (V4 memory-mapped peripherals):
;     0x0080 = GPIO OUT    (write = set pins, read = see them)
;     0x0081 = GPIO IN     (read input pins)
;     0x0082 = TIMER       (read-only: free-running 16-bit counter)
;     0x0083 = SENSOR      (read-only: ring oscillator pulse counter)
;     0x0084 = MSR/P-bit   (read/write: bit 0 = P-bit)
;     0x0085 = WAIT        (write = sleep until heartbeat if P=0)
;
;  RAM at HALT (the testbench checks these):
;     RAM[0] = TIMER snapshot  (non-zero)
;     RAM[1] = SENSOR snapshot (depends on ring oscillator speed)
;     RAM[2] = P-bit readback  (0 in eco, 1 in turbo)
;  GPIO at HALT:
;     0xEC01 = ran in ECO and WOKE UP from sleep   (slow ring = cool)
;     0x700C = ran in TURBO and raced on           (fast ring = hot)
; ============================================================================

        LDI   R6, 0          ; R6 = constant ZERO
        LDI   R7, 1          ; R7 = constant ONE
        LDI   R0, 0          ; R0 = RAM write index

; ---- Step 1: Read TIMER (address 0x0082) and store to RAM -----------------
        LDI   R4, 0x82       ; R4 = TIMER address
        LDM   R1, R4, R6     ; R1 = TIMER value (memory-mapped read)
        STM   R1, [R6+R0]    ; RAM[0] = TIMER snapshot
        ADD   R0, R0, R7     ; index++

; ---- Step 2: Read SENSOR (address 0x0083) and store to RAM ----------------
        LDI   R4, 0x83       ; R4 = SENSOR address
        LDM   R2, R4, R6     ; R2 = SENSOR value (ring osc pulse count)
        STM   R2, [R6+R0]    ; RAM[1] = SENSOR snapshot
        ADD   R0, R0, R7     ; index++

; ---- Step 3: SIGNED compare — is SENSOR >= 3? -----------------------------
        LDI   R3, 3          ; R3 = threshold ("hot" if at or above it;
                             ;      3 = demo value - real silicon would
                             ;      calibrate this from measurements)
        SUB   R5, R2, R3     ; R5 = SENSOR - 3 (two's complement)
        LDI   R4, 15         ; shift amount = 15 (top bit = the sign bit)
        SRA   R4, R5, R4     ; R4 = 0xFFFF if SENSOR < 3, else 0x0000
        BNEZ  R4, eco        ; negative result -> cool chip -> ECO mode

; ---- TURBO MODE: P = 1 (sensor >= threshold = "hot") ----------------------
turbo:  LDI   R1, 1          ; P-bit = 1 (turbo mode)
        LDI   R4, 0x84       ; P-bit address
        STM   R1, [R4+R6]    ; write P = 1
        LDI   R5, 0x70       ; build the marker 0x700B ("TURB")
        LDI   R3, 8
        SLL   R5, R5, R3     ; 0x70 << 8 = 0x7000
        LDI   R3, 0x0B
        OR    R5, R5, R3     ; R5 = 0x700B
        BEQZ  R6, show       ; R6=0 always -> jump over the eco branch

; ---- ECO MODE: P = 0 (sensor < threshold = "cool") ------------------------
eco:    LDI   R1, 0          ; P-bit = 0 (eco mode)
        LDI   R4, 0x84       ; P-bit address
        STM   R1, [R4+R6]    ; write P = 0
        LDI   R5, 0xEC       ; build the marker 0xEC00 ("ECO")
        LDI   R3, 8
        SLL   R5, R5, R3     ; 0xEC << 8 = 0xEC00
                             ; (falls through into show)

; ---- Step 4: Show the mode marker on GPIO ---------------------------------
show:   LDI   R4, 0x80       ; GPIO OUT address
        STM   R5, [R4+R6]    ; GPIO = 0xEC00 (eco) or 0x700B (turbo)

; ---- Step 5: THE WAIT — the power-saving heart of the P-bit ---------------
;    Writing 0x0085 asks to sleep. The hardware decides:
;      P=0 -> CPU freezes until TIMER[15] rises (heartbeat)
;      P=1 -> request ignored, CPU keeps racing (heat is our ally)
        LDI   R4, 0x85       ; WAIT register address
        STM   R7, [R4+R6]    ; any write triggers the WAIT logic

; ---- Step 6: Read the P-bit back and store to RAM --------------------------
        LDI   R4, 0x84       ; P-bit address
        LDM   R3, R4, R6     ; R3 = P-bit readback
        STM   R3, [R6+R0]    ; RAM[2] = P-bit readback
        ADD   R0, R0, R7     ; index++

; ---- Step 7: The wake-up proof ---------------------------------------------
;    These three instructions only execute AFTER the sleep is over
;    (or immediately, in turbo). If the CPU never woke up, GPIO would
;    stay at the plain marker. The +1 is the heartbeat's receipt.
        ADD   R5, R5, R7     ; marker + 1  -> 0xEC01 eco-awake / 0x700C turbo
        LDI   R4, 0x80       ; GPIO OUT address
        STM   R5, [R4+R6]    ; GPIO = the "I am awake" receipt

        HALT                 ; freeze - the testbench checks everything
