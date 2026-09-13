#!/usr/bin/env python3
# =====================================================================
# run_experiments.py - the three TELUGU T-16 silicon-physics experiments
#
# WHAT THIS RUNS (all with the REAL SkyWater sky130 tt-corner models,
# bundled in spice/sky130_models/ - no PDK installation needed):
#
#   EXP1  ro_vdd_sweep.csv
#         The 15-stage ring oscillator vs supply voltage, 0.10 V to
#         1.80 V. This is the heart curve of the whole project: how
#         far into the sub-threshold regime does the ring keep
#         beating, and how fast. (Simulation truth; silicon truth
#         comes after the shuttle.)
#
#   EXP2  ro_temp_scissors.csv
#         The same ring at a fixed VDD while temperature sweeps
#         -20 C to +85 C, at VDD = 0.30 V (sub-threshold) AND
#         VDD = 1.80 V (super-threshold). The two curves move in
#         OPPOSITE directions - inverse temperature dependence.
#         This is the physics the P-bit rides on.
#
#   EXP3  fbb_vth_shift.csv
#         Forward body bias on the NFET: Vth extracted (constant
#         current, 100 nA x W/L) at several body-source voltages.
#         This quantifies the honest circuit-level answer to the
#         "can I get Vth down to 0.12-0.15 V" question: the FAB
#         threshold stays what it is, but the CIRCUIT sees a lower
#         effective threshold - for as long as the junction stays
#         off and you accept the leakage bill.
#
# REQUIREMENTS: ngspice on PATH (Ubuntu/WSL: sudo apt install ngspice)
#
# RUN:  python3 spice/run_experiments.py           (all three)
#       python3 spice/run_experiments.py --only 1  (just experiment 1)
#
# Outputs go to results/ next to this script (created automatically).
# Every ngspice deck is kept in spice/work/ so you can open, edit and
# re-run any single point yourself.
#
# Project: TELUGU T-16 (TG16 ISA v1.0)
# License: Apache-2.0 (sky130 model files (c) 2020 The SkyWater PDK
#          Authors, Apache-2.0)
# =====================================================================
import os, re, sys, shutil, subprocess, math

HERE    = os.path.dirname(os.path.abspath(__file__))
LIB     = os.path.join(HERE, "sky130_models", "models", "corners", "tt_mini.spice")
WORK    = os.path.join(HERE, "work")
OUTDIR  = os.environ.get("T16_SPICE_OUT", os.path.join(HERE, "results"))
NGSPICE = os.environ.get("NGSPICE", "ngspice")

os.makedirs(WORK, exist_ok=True)
os.makedirs(OUTDIR, exist_ok=True)

# ---------------------------------------------------------------
# deck helpers
# ---------------------------------------------------------------
RO_STAGES = """
.subckt t16_inv a y vdd
XN y a 0 0 sky130_fd_pr__nfet_01v8 w=1 l=0.15
XP y a vdd vdd sky130_fd_pr__pfet_01v8 w=2 l=0.15
.ends
"""

def ro_deck(vdd, temp, dur, step, name, r1=3, r2=13):
    half = vdd / 2.0
    nper = r2 - r1
    inv = "\n".join(f"Xi{i} n{i} n{i+1} vdd t16_inv" for i in range(1, 16))
    # wrap the ring: last inverter feeds the first node
    inv = inv.replace("Xi15 n15 n16 vdd t16_inv", "Xi15 n15 n1 vdd t16_inv")
    return f"""* T-16 ring oscillator: {name}
.option scale=1.0u
.temp {temp}
.include "{LIB}"
.param VDD={vdd}
Vdd vdd 0 {{VDD}}
{RO_STAGES}
{inv}
.ic v(n1)={vdd*0.3:.6f}
.control
tran {step} {dur} uic
meas tran t1 WHEN v(n1)={half:.9f} RISE={r1}
meas tran t2 WHEN v(n1)={half:.9f} RISE={r2}
let freq = 1/((t2-t1)/{nper})
echo FREQ_RESULT
print freq
.endc
.end
"""

def run_ngspice(deck_text, tag):
    """Run one deck; return dict of measured scalars, or None on failure."""
    path = os.path.join(WORK, tag + ".spice")
    with open(path, "w") as f:
        f.write(deck_text)
    try:
        r = subprocess.run([NGSPICE, "-b", path], capture_output=True,
                           text=True, timeout=300)
    except subprocess.TimeoutExpired:
        print(f"    {tag}: TIMEOUT")
        return None
    out = r.stdout + r.stderr
    m = {}
    for key in ("t1", "t2", "freq"):
        mm = re.search(rf"^{key}\s*=\s*([-\d.eE+]+)", out, re.M)
        if mm:
            m[key] = float(mm.group(1))
    if "freq" not in m:
        return None
    return m

# ---------------------------------------------------------------
# EXP 1 - ring frequency vs VDD
# ---------------------------------------------------------------
def exp1():
    print("EXP1: ring oscillator frequency vs VDD (the heart curve)")
    print("      note: below ~0.24 V the ring beats only a few times per")
    print("      millisecond, so those points measure 2 periods, not 10;")
    print("      points marked NO OSCILLATION simply did not complete a")
    print("      beat inside the simulated window - not proof of death.")
    # (vdd, duration, step, rise_from, rise_to)
    # Below 0.24 V the transient cost explodes and the ring may take
    # milliseconds per beat: those points get a 1 ms window and NO retry -
    # a 'no beat in window' there is an honest measurement floor, not a
    # claim that oscillation is impossible.
    points = [
        (0.10, "1ms",  "5ns",  2, 4),
        (0.12, "1ms",  "5ns",  2, 4),
        (0.14, "1ms",  "5ns",  2, 4),
        (0.16, "1ms",  "5ns",  2, 4),
        (0.18, "1ms",  "5ns",  2, 4),
        (0.20, "1ms",  "5ns",  2, 4),
        (0.22, "1ms",  "5ns",  2, 4),
        (0.24, "2ms",  "10ns", 3, 13),
        (0.26, "2ms",  "10ns", 3, 13),
        (0.28, "2ms",  "10ns", 3, 13),
        (0.30, "2ms",  "10ns", 3, 13),
        (0.34, "1ms",  "5ns",  3, 13),
        (0.40, "400us","2ns",  3, 13),
        (0.50, "200us","1ns",  3, 13),
        (0.70, "40us", "0.2ns",3, 13),
        (0.90, "20us", "0.1ns",3, 13),
        (1.20, "20ns", "0.05ns",3, 13),
        (1.50, "20ns", "0.05ns",3, 13),
        (1.80, "20ns", "0.05ns",3, 13),
    ]
    rows = []
    for vdd, dur, step, r1, r2 in points:
        tag = f"ro_vdd_{vdd:.2f}"
        m = run_ngspice(ro_deck(vdd, 27, dur, step, tag, r1, r2), tag)
        if m is None and vdd >= 0.24:
            # retry (fast points only) with a 2x longer window
            dur2 = f"{float(dur[:-2])*2}{dur[-2:]}"
            m = run_ngspice(ro_deck(vdd, 27, dur2, step, tag + "_retry", r1, r2),
                            tag + "_retry")
        if m and m["freq"] > 0 and m["freq"] < 1e12:
            f = m["freq"]
            p = 1.0 / f
            print(f"    VDD={vdd:.2f} V   period={p:12.4e} s   freq={f:12.4e} Hz")
            rows.append((vdd, p, f))
        else:
            print(f"    VDD={vdd:.2f} V   NO OSCILLATION (within the simulated window)")
            rows.append((vdd, None, None))
    with open(os.path.join(OUTDIR, "ro_vdd_sweep.csv"), "w") as f:
        f.write("vdd_v,period_s,freq_hz\n")
        for vdd, p, fr in rows:
            f.write(f"{vdd},{'' if p is None else p},{'' if fr is None else fr}\n")
    ok = sum(1 for r in rows if r[2])
    print(f"  -> {os.path.join(OUTDIR, 'ro_vdd_sweep.csv')}  ({ok}/{len(rows)} points oscillating)")

# ---------------------------------------------------------------
# EXP 2 - temperature scissors (inverse temperature dependence)
# ---------------------------------------------------------------
def exp2():
    print("EXP2: temperature scissors - same ring, VDD=0.30 V and 1.80 V")
    temps = [-20, -10, 0, 10, 27, 40, 55, 70, 85]
    out = {}
    for vdd, dur, step in ((0.30, "2ms", "10ns"), (1.80, "20ns", "0.05ns")):
        rows = []
        for t in temps:
            tag = f"ro_temp_{vdd:.2f}_{t}"
            m = run_ngspice(ro_deck(vdd, t, dur, step, tag), tag)
            if m and m["freq"] > 0:
                rows.append((t, 1.0 / m["freq"], m["freq"]))
                print(f"    VDD={vdd:.2f} T={t:+3d} C  freq={m['freq']:12.4e} Hz")
            else:
                rows.append((t, None, None))
                print(f"    VDD={vdd:.2f} T={t:+3d} C  NO OSCILLATION")
        out[vdd] = rows
    with open(os.path.join(OUTDIR, "ro_temp_scissors.csv"), "w") as f:
        f.write("vdd_v,temp_c,period_s,freq_hz\n")
        for vdd in sorted(out):
            for t, p, fr in out[vdd]:
                f.write(f"{vdd},{t},{'' if p is None else p},{'' if fr is None else fr}\n")
    # quick honest verdict straight from the data
    try:
        f03 = [r[2] for r in out[0.30] if r[2]]
        f18 = [r[2] for r in out[1.80] if r[2]]
        if len(f03) > 2 and len(f18) > 2:
            d03 = (f03[-1] / f03[0] - 1) * 100
            d18 = (f18[-1] / f18[0] - 1) * 100
            print(f"  sub-threshold (0.30 V): frequency changed {d03:+.1f}% from -20C to +85C")
            print(f"  super-threshold (1.80 V): frequency changed {d18:+.1f}% from -20C to +85C")
            print("  (positive = speeds up when hot = inverse temperature dependence)")
    except Exception:
        pass
    print(f"  -> {os.path.join(OUTDIR, 'ro_temp_scissors.csv')}")

# ---------------------------------------------------------------
# EXP 3 - forward body bias: effective Vth shift
# ---------------------------------------------------------------
FBB_DECK = """* NFET effective-Vth vs forward body-source bias
.option scale=1.0u
.temp 27
.include "{lib}"
.param VBS={vbs}
XD d g 0 b sky130_fd_pr__nfet_01v8 w=1 l=0.15
VBS b 0 {{VBS}}
VDS d 0 0.05
VGS g 0 0
.control
dc VGS 0 1.0 0.005
let id = -i(VDS)
wrdata {data} id v(g)
.endc
.end
"""

def extract_vth(data_pairs, w, l, i_factor=100e-9):
    """Constant-current Vth: Id_target = i_factor * W/L (100 nA * W/L)."""
    target = i_factor * (w / l)
    prev = None
    for vgs, iid in data_pairs:
        if prev and prev[1] < target <= iid:
            # linear interpolation between the two samples
            v0, i0 = prev
            return v0 + (target - i0) * (vgs - v0) / (iid - i0)
        prev = (vgs, iid)
    return None

def exp3():
    print("EXP3: forward body bias - effective Vth of the NFET (W=1u, L=0.15u)")
    vbs_list = [0.0, 0.15, 0.30, 0.45, 0.60]
    rows = []
    for vbs in vbs_list:
        tag = f"fbb_{vbs:.2f}".replace(".", "p")
        datafile = os.path.join(WORK, tag + ".data")
        deck = FBB_DECK.format(lib=LIB, vbs=vbs, data=tag + ".data")
        path = os.path.join(WORK, tag + ".spice")
        with open(path, "w") as f:
            f.write(deck)
        try:
            subprocess.run([NGSPICE, "-b", tag + ".spice"], capture_output=True,
                           text=True, timeout=120, cwd=WORK)
        except subprocess.TimeoutExpired:
            print(f"    VBS={vbs:.2f}: TIMEOUT")
            rows.append((vbs, None))
            continue
        pairs = []
        layout = None   # None=undetected, "sweep_first", "value_first"
        with open(datafile) as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 4:
                    try:
                        # ngspice wrdata writes one (scale, value) pair per
                        # vector, so a DC sweep of VGS with 'wrdata f id v(g)'
                        # produces 4 columns. ngspice 44 writes the sweep
                        # (scale) column FIRST:  vgs id vgs v(g)
                        # some older builds write the value first: id vgs v(g) vgs
                        # Detect once from the first line: in the
                        # sweep-first layout col1 == col3 (same sweep value).
                        if layout is None:
                            layout = "sweep_first" if parts[0] == parts[2] else "value_first"
                        if layout == "sweep_first":
                            iid = float(parts[1])
                            vgs = float(parts[3])
                        else:
                            iid = float(parts[0])
                            vgs = float(parts[2])
                        pairs.append((vgs, abs(iid)))
                    except ValueError:
                        pass
        vth = extract_vth(pairs, 1.0, 0.15)
        if vth is not None:
            print(f"    VBS={vbs:+.2f} V   effective Vth = {vth:.4f} V")
        else:
            print(f"    VBS={vbs:+.2f} V   Vth extraction FAILED")
        rows.append((vbs, vth))
    with open(os.path.join(OUTDIR, "fbb_vth_shift.csv"), "w") as f:
        f.write("vbs_v,vth_const_current_v\n")
        for vbs, vth in rows:
            f.write(f"{vbs},{'' if vth is None else vth}\n")
    if rows[0][1] is not None and rows[-1][1] is not None:
        shift = rows[0][1] - rows[-1][1]
        print(f"  -> Vth dropped by {shift:.3f} V from VBS=0 to VBS={rows[-1][0]} V")
        print(f"     (the fab's Vth did NOT change - the circuit merely sees it lower;")
        print(f"      the price is junction leakage and, past ~0.6 V, a conducting diode)")
    print(f"  -> {os.path.join(OUTDIR, 'fbb_vth_shift.csv')}")

# ---------------------------------------------------------------
if __name__ == "__main__":
    only = None
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1]
    if not os.path.exists(LIB):
        print(f"ERROR: bundled sky130 library not found at {LIB}")
        sys.exit(1)
    if only in (None, "1"):
        exp1()
    if only in (None, "2"):
        exp2()
    if only in (None, "3"):
        exp3()
    print("\nAll requested experiments complete.")
