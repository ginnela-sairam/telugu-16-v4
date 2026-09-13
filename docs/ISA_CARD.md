# T-16 V4.1 Instruction Set Architecture (ISA) Card

## Register File
| Register | Name | Notes |
|----------|------|-------|
| R0 | General | Free to use |
| R1 | General | Free to use |
| R2 | General | Free to use |
| R3 | General | Free to use |
| R4 | General | Commonly used for addresses |
| R5 | General | Free to use |
| R6 | General | Commonly set to 0 (zero register) |
| R7 | General / LR | Used as link register by JAL |

## Instruction Encoding

### Register format (R-type)
```
 15 14 13 12 | 11 10 9 | 8 7 6 | 5 4 3 | 2 1 0
    opcode   |   Rd    |  Ra   |  Rb   | func
```

### Immediate format (I-type)
```
 15 14 13 12 | 11 10 9 | 8 7 6 5 4 3 2 1 0
    opcode   |   Rd    |    imm9 (signed)
```

## Instructions

| Opcode | Hex | Mnemonic | Format | Operation |
|--------|-----|----------|--------|-----------|
| 0000 | 0 | ADD | R | Rd = Ra + Rb |
| 0001 | 1 | SUB | R | Rd = Ra - Rb |
| 0010 | 2 | AND | R | Rd = Ra & Rb |
| 0011 | 3 | OR  | R | Rd = Ra \| Rb |
| 0100 | 4 | XOR | R | Rd = Ra ^ Rb |
| 0101 | 5 | SLL | R | Rd = Ra << Rb[3:0] (func=0) |
| 0101 | 5 | SRL | R | Rd = Ra >> Rb[3:0] (func=1) |
| 0101 | 5 | SRA | R | Rd = Ra >>> Rb[3:0] (func=2+) |
| 0110 | 6 | LDI | I | Rd = sign_extend(imm9) |
| 0111 | 7 | LDM | R | Rd = MEM[Ra + Rb] |
| 1000 | 8 | STM | R | MEM[Ra + Rb] = Rd |
| 1010 | A | BEQZ | I | if(Rd==0) PC = PC + 1 + sext(imm9) |
| 1011 | B | BNEZ | I | if(Rd!=0) PC = PC + 1 + sext(imm9) |
| 1100 | C | JAL | I | Rd = PC + 1; PC = PC + 1 + sext(imm9) |
| 1101 | D | JR  | R | PC = Rd |
| 1111 | F | HALT | - | Stop CPU |

## V4.1 Memory-Mapped Peripherals

Access via LDM/STM with the peripheral address:

| Address | Name | Access | Description |
|---------|------|--------|-------------|
| 0x0000-0x007F | RAM | R/W | 128 words × 16 bits |
| 0x0080 | GPIO_OUT | R/W | 16-bit output pins |
| 0x0081 | GPIO_IN | R | 16-bit input pins |
| 0x0082 | TIMER | R | 16-bit free-running counter |
| 0x0083 | SENSOR | R | Ring oscillator pulse counter |
| 0x0084 | MSR | R/W | P-bit (bit 0): 0=eco, 1=turbo |
| 0x0085 | WAIT | W | Write any value: sleep if P=0 |

## Clock Modes

| Mode | clksel | Source | Use Case |
|------|--------|--------|----------|
| External | 0 | clk pin | Normal demo, measurement |
| Self-clock | 1 | RO/32 | Ultra-low-VDD record experiment |

## Example: Read SENSOR and set P-bit

```asm
    LDI  R6, 0          ; zero constant
    LDI  R4, 0x83       ; SENSOR address
    LDM  R2, R4, R6     ; R2 = SENSOR value
    LDI  R3, 10         ; threshold
    SUB  R5, R2, R3     ; R5 = SENSOR - threshold
    BNEZ R5, turbo       ; if non-zero → turbo
    ; eco path:
    LDI  R1, 0
    LDI  R4, 0x84
    STM  R1, [R4+R6]    ; P = 0
    BEQZ R6, done
turbo:
    LDI  R1, 1
    LDI  R4, 0x84
    STM  R1, [R4+R6]    ; P = 1
done:
    HALT
```
