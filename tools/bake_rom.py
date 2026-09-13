#!/usr/bin/env python3
# ============================================================================
#  bake_rom.py — bake a program into rtl/t16_rom.v for SILICON (V4.1)
# ----------------------------------------------------------------------------
#  WHY THIS EXISTS:
#    In simulation, the ROM loads your .hex file with $readmemh — easy.
#    But in the OpenLane Docker container (and on TinyTapeout's build
#    servers), relative file paths break, and a missing file makes the
#    whole ROM undefined. So for silicon we WRITE the program directly
#    into rtl/t16_rom.v as Verilog assignments between two markers.
#    Yosys then turns those constants into real gates. No files to find.
#
#  HOW TO USE:
#    python3 tools/bake_rom.py sw/program_fib.hex      # bake Fibonacci
#    python3 tools/bake_rom.py sw/program_pbit.hex     # bake the P-bit demo
#
#  THEN re-run the tests (the baked words are overridden in simulation by
#  the .hex files, so nothing changes for run_sim.sh) and re-run the
#  OpenLane flow so the new program reaches the GDS.
# ============================================================================

import os
import re
import sys

ROM_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "..", "rtl", "t16_rom.v")

BEGIN_MARK = "//    ---- T16_ROM_BAKE_BEGIN (do not edit by hand) ----"
END_MARK   = "//    ---- T16_ROM_BAKE_END ----"


def read_hex_words(path):
    """Read a t16asm .hex file -> list of (address, word, comment)."""
    words = []
    with open(path, "r") as f:
        for line_no, raw in enumerate(f, 1):
            line = raw.split("//")[0].strip()   # drop comments
            if not line:
                continue
            token = line.split()[0].upper()
            if not re.fullmatch(r"[0-9A-F]{1,4}", token):
                raise SystemExit("ERROR: %s line %d: '%s' is not a hex word"
                                 % (path, line_no, token))
            comment = raw.split("//", 1)[1].strip() if "//" in raw else ""
            words.append((len(words), int(token, 16), comment))
    return words


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 tools/bake_rom.py <program.hex>")
        print("Example: python3 tools/bake_rom.py sw/program_fib.hex")
        sys.exit(1)

    hex_path = sys.argv[1]
    if not os.path.isfile(hex_path):
        print("ERROR: cannot read %s" % hex_path)
        sys.exit(1)

    words = read_hex_words(hex_path)

    with open(ROM_FILE, "r") as f:
        rom_src = f.read()

    if BEGIN_MARK not in rom_src or END_MARK not in rom_src:
        print("ERROR: bake markers not found in rtl/t16_rom.v")
        print("       (they were introduced in V4.1 — is the file intact?)")
        sys.exit(1)

    # Build the replacement block. Only REAL instructions are baked —
    # untouched words stay at the HALT default set by the initial loop.
    lines = [BEGIN_MARK]
    for addr, word, comment in words:
        if word == 0xF000 and not comment:
            continue                      # HALT padding: default already covers it
        c = "// " + comment if comment else ""
        lines.append("        mem[%3d]  = 16'h%04X;  %s" % (addr, word, c))
    lines.append("        " + END_MARK)
    new_block = "\n".join(lines)

    pattern = re.compile(re.escape(BEGIN_MARK) + r".*?" + re.escape(END_MARK),
                         re.DOTALL)
    rom_src = pattern.sub(new_block, rom_src, count=1)

    with open(ROM_FILE, "w") as f:
        f.write(rom_src)

    real = sum(1 for a, w, c in words if w != 0xF000 or c)
    print("Baked OK: %d words (%d real instructions) from %s into rtl/t16_rom.v"
          % (len(words), real, hex_path))
    print("Simulation is unchanged ($readmemh still overrides in sim).")
    print("Re-run the OpenLane flow so the new program reaches the GDS.")


if __name__ == "__main__":
    main()
