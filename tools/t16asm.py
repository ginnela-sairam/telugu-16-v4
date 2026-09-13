#!/usr/bin/env python3
# ============================================================================
#  t16asm.py - the tiny T-16 assembler
# ----------------------------------------------------------------------------
#  WHAT IT DOES: turns your human-readable program (.asm) into machine code
#                (.hex) that the T-16 ROM understands.
#
#  HOW TO USE (works the same on Windows Python 3 and inside WSL):
#      python3 t16asm.py program.asm program.hex
#
#  THE LANGUAGE IT SPEAKS (one instruction per line):
#
#      ; text after a semicolon is a comment (ignored)
#      loop:                        <- a LABEL marks a place to jump to
#      LDI   R1, 10                 <- put the number 10 into register R1
#      ADD   R3, R1, R2             <- R3 = R1 + R2
#      SUB   R4, R1, R2             <- R4 = R1 - R2
#      AND   R3, R1, R2             <- R3 = R1 AND R2  (bit by bit)
#      OR    R3, R1, R2             <- R3 = R1 OR R2
#      XOR   R3, R1, R2             <- R3 = R1 XOR R2
#      SLL   R3, R1, R2             <- R3 = R1 shifted LEFT  by R2
#      SRL   R3, R1, R2             <- R3 = R1 shifted RIGHT by R2 (zeroes)
#      SRA   R3, R1, R2             <- R3 = R1 shifted RIGHT by R2 (sign kept)
#      LDM   R1, R2, R3             <- R1 = memory[R2 + R3]
#      STM   R1, R2, R3             <- memory[R2 + R3] = R1
#      BEQZ  R1, loop               <- if R1 == 0, jump to the label
#      BNEZ  R1, loop               <- if R1 != 0, jump to the label
#      JAL   R5, my_sub             <- call: jump there, remember return point in R5
#      JR    R5                     <- return: jump to the address inside R5
#      NOP                          <- do nothing for one cycle
#      HALT                         <- stop the CPU forever
#
#  NUMBERS can be decimal (10), negative (-256), or hex (0x80).
# ============================================================================

import sys

# ----------------------------------------------------------------------------
# The machine's dictionary: name -> (opcode number, operand pattern)
#   'rrr'   = three registers          Rd, Ra, Rb
#   'ri'    = register + immediate     Rd, number
#   'rl'    = register + label/number  Rd, where-to-jump
#   'r'     = one register             Rd
#   'none'  = no operands
# ----------------------------------------------------------------------------
OPS = {
    'ADD':  (0x0, 'rrr'),
    'SUB':  (0x1, 'rrr'),
    'AND':  (0x2, 'rrr'),
    'OR':   (0x3, 'rrr'),
    'XOR':  (0x4, 'rrr'),
    'SLL':  (0x5, 'rrr_f0'),
    'SRL':  (0x5, 'rrr_f1'),
    'SRA':  (0x5, 'rrr_f2'),
    'LDI':  (0x6, 'ri'),
    'LDM':  (0x7, 'rrr'),
    'STM':  (0x8, 'rrr'),
    'BEQZ': (0xA, 'rl'),
    'BNEZ': (0xB, 'rl'),
    'JAL':  (0xC, 'rl'),
    'JR':   (0xD, 'r'),
    'NOP':  (0x9, 'none'),
    'HALT': (0xF, 'none'),
}

MAX_WORDS = 256          # ROM size: 256 instructions


def parse_register(text, where):
    """'R3' -> 3. Anything else is an error."""
    t = text.strip().upper()
    if len(t) == 2 and t[0] == 'R' and t[1].isdigit() and 0 <= int(t[1]) <= 7:
        return int(t[1])
    raise SyntaxError("%s: '%s' is not a register (use R0..R7)" % (where, text))


def parse_number(text, where):
    """'10' -> 10, '-256' -> -256, '0x80' -> 128."""
    t = text.strip()
    try:
        if t.lower().startswith('0x'):
            return int(t, 16)
        return int(t, 10)
    except ValueError:
        raise SyntaxError("%s: '%s' is not a number" % (where, text))


def imm9(value, where):
    """Fold a number into 9 bits (allowed range: -256 .. +255)."""
    if value < -256 or value > 255:
        raise SyntaxError("%s: %d does not fit in 9 bits (-256..255)" % (where, value))
    return value & 0x1FF


def tokenize(line):
    """Split one source line into clean pieces.
    Handles commas, brackets like [R4+R0], and strips comments."""
    out = []
    token = ''
    for ch in line:
        if ch == ';':                      # comment starts - stop reading this line
            break
        if ch in ' \t,[]+':                # separators
            if token:
                out.append(token)
                token = ''
        else:
            token += ch
    if token:
        out.append(token)
    return out


def assemble(source_text, source_name="program"):
    """Two passes: pass 1 finds labels, pass 2 writes machine code."""
    labels = {}
    words = []          # list of (opcode_info, tokens, line_number, source_line)
    line_no = 0

    # ---------- PASS 1: read every line, remember labels ----------
    for raw_line in source_text.splitlines():
        line_no += 1
        line = raw_line.replace('\r', '')          # survive Windows line endings
        tokens = tokenize(line)
        if not tokens:
            continue                               # empty line
        where = "%s line %d" % (source_name, line_no)

        # A label? (word ending in ':', possibly followed by an instruction)
        if tokens[0].upper().endswith(':'):
            label = tokens[0][:-1]
            if not label.replace('_', '').isalnum():
                raise SyntaxError("%s: bad label name '%s'" % (where, label))
            if label.upper() in OPS:
                raise SyntaxError("%s: label '%s' clashes with an instruction name"
                                  % (where, label))
            labels[label] = len(words)
            tokens = tokens[1:]
            if not tokens:
                continue                           # label alone on its line

        # An instruction?
        mnem = tokens[0].upper()
        if mnem not in OPS:
            raise SyntaxError("%s: unknown instruction '%s'" % (where, tokens[0]))
        words.append((OPS[mnem], tokens[1:], where, ' '.join(tokens)))

    if len(words) > MAX_WORDS:
        raise SyntaxError("program too big: %d instructions (ROM holds %d)"
                          % (len(words), MAX_WORDS))

    # ---------- PASS 2: encode each instruction ----------
    hex_lines = []
    for addr, (opinfo, args, where, clean) in enumerate(words):
        opcode, pattern = opinfo
        word = (opcode << 12)

        if pattern == 'rrr' or pattern.startswith('rrr_f'):
            if len(args) != 3:
                raise SyntaxError("%s: needs 3 registers, e.g. ADD Rd, Ra, Rb" % where)
            rd = parse_register(args[0], where)
            ra = parse_register(args[1], where)
            rb = parse_register(args[2], where)
            word |= (rd << 9) | (ra << 6) | (rb << 3)
            if pattern.startswith('rrr_f'):        # shift family: func bits
                word |= int(pattern[-1])

        elif pattern == 'ri':                      # LDI Rd, imm9
            if len(args) != 2:
                raise SyntaxError("%s: needs a register and a number: LDI Rd, number" % where)
            rd = parse_register(args[0], where)
            word |= (rd << 9) | imm9(parse_number(args[1], where), where)

        elif pattern == 'rl':                      # branches and calls
            if len(args) != 2:
                raise SyntaxError("%s: needs a register and a destination label" % where)
            rd = parse_register(args[0], where)
            word |= (rd << 9)
            target_text = args[1]
            if target_text in labels:              # jump to a LABEL
                target = labels[target_text]
                offset = target - (addr + 1)       # counted from the NEXT line
            else:                                  # ...or a raw number
                offset = parse_number(target_text, where)
            word |= imm9(offset, where)

        elif pattern == 'r':                       # JR Rd
            if len(args) != 1:
                raise SyntaxError("%s: needs one register: JR Rd" % where)
            rd = parse_register(args[0], where)
            word |= (rd << 9)

        elif pattern == 'none':                    # NOP / HALT
            if args:
                raise SyntaxError("%s: takes no operands" % where)

        hex_lines.append("%04X // %03d: %s" % (word, addr, clean))

    # Pad the rest of the 256-word ROM with HALT instructions.
    # Why? If a bug ever makes the CPU run past the end of your program,
    # it lands on HALT padding and stops safely instead of executing garbage.
    if len(hex_lines) < MAX_WORDS:
        hex_lines.append("%04X // --- safety padding: the rest is HALT ---"
                         % 0xF000)
        while len(hex_lines) < MAX_WORDS:
            hex_lines.append("F000")

    return hex_lines


def main():
    if len(sys.argv) != 3:
        print("Usage: python3 t16asm.py input.asm output.hex")
        print("Example: python3 t16asm.py sw/program_fib.asm sw/program_fib.hex")
        sys.exit(1)

    src_path, dst_path = sys.argv[1], sys.argv[2]

    try:
        with open(src_path, 'r') as f:
            source_text = f.read()
    except IOError as e:
        print("ERROR: cannot read %s (%s)" % (src_path, e))
        sys.exit(1)

    try:
        hex_lines = assemble(source_text, src_path)
    except SyntaxError as e:
        print("ERROR: %s" % e)
        sys.exit(1)

    with open(dst_path, 'w') as f:
        f.write('\n'.join(hex_lines) + '\n')

    print("Assembled OK: %d instructions -> %s" % (len(hex_lines), dst_path))


if __name__ == '__main__':
    main()
