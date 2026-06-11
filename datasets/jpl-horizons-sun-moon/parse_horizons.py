#!/usr/bin/env python3
"""Deterministic parser: _raw_horizons_{moon,sun}.txt -> sun_moon_daily.csv.
Also emits ../tidal-manila/tidal_derived.csv (lunar+solar tidal accel from the
Horizons distances, lab convention value=C/d^3; C_moon=2.998598e11 g*m^3
[r=0.300 m via 2GMr/g0], C_sun=8.121786e18 g*m^3 = C_moon*(M_sun/M_moon)).
Source of record: NASA/JPL Horizons (DE441), airless apparent az/el, topocentric
PCSO Mandaluyong (121.0359 E, 14.5794 N), daily 13:00:02.88 UT (= 21:00 PHT).
"""
import os, csv, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
AU_KM = 149597870.700
C_MOON = 2.998598e11      # g*m^3 (recovered from legacy file; r=0.300 m)
C_SUN = 8.121786e18       # g*m^3 (same r, M_sun/M_moon = 27,090,711)
MON = {m: i+1 for i, m in enumerate(
    ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"])}

def parse(path, n_fields):
    rows = {}
    with open(path) as f:
        in_block = False
        for line in f:
            line = line.rstrip("\n")
            if line.startswith("$$SOE"): in_block = True; continue
            if line.startswith("$$EOE"): break
            if not in_block: continue
            date_str = line[1:12]                     # e.g. 2025-Jun-11
            body = line[28:]                          # after time + presence-flag cols
            vals = body.split()
            assert len(vals) == n_fields, (path, line)
            y, mo, d = date_str.split("-")
            iso = f"{y}-{MON[mo]:02d}-{int(d):02d}"
            rows[iso] = [float(v) for v in vals]
    return rows

def main():
    moon = parse(os.path.join(HERE, "_raw_horizons_moon.txt"), 5)  # az el illu% delta deldot
    sun = parse(os.path.join(HERE, "_raw_horizons_sun.txt"), 4)    # az el delta deldot
    assert len(moon) == 366 and len(sun) == 366, (len(moon), len(sun))
    assert set(moon) == set(sun)
    dates = sorted(moon)
    # continuity: every calendar day present
    d0 = datetime.date.fromisoformat(dates[0])
    for i, ds in enumerate(dates):
        assert datetime.date.fromisoformat(ds) == d0 + datetime.timedelta(days=i), ds
    out = os.path.join(HERE, "sun_moon_daily.csv")
    tid = os.path.join(HERE, "..", "tidal-manila", "tidal_derived.csv")
    with open(out, "w", newline="") as f1, open(tid, "w", newline="") as f2:
        w1 = csv.writer(f1); w2 = csv.writer(f2)
        w1.writerow(["Date","Moon Az (deg)","Moon Alt (deg)","Moon Illum (0-1)",
                     "Moon Dist (km)","Sun Az (deg)","Sun Alt (deg)","Sun Dist (km)"])
        w2.writerow(["Date","Moon Dist (km)","Lunar tidal accel (g)",
                     "Sun Dist (km)","Solar tidal accel (g)","Total tidal accel (g)"])
        for ds in dates:
            maz, mel, illu, mdelta, _ = moon[ds]
            saz, sel, sdelta, _ = sun[ds]
            mkm = mdelta * AU_KM; skm = sdelta * AU_KM
            lt = C_MOON / (mkm*1000)**3; st = C_SUN / (skm*1000)**3
            w1.writerow([ds, f"{maz:.6f}", f"{mel:.6f}", f"{illu/100:.5f}",
                         f"{mkm:.1f}", f"{saz:.6f}", f"{sel:.6f}", f"{skm:.0f}"])
            w2.writerow([ds, f"{mkm:.1f}", f"{lt:.4e}", f"{skm:.0f}",
                         f"{st:.4e}", f"{lt+st:.4e}"])
    print(f"wrote {out} and {tid}: {len(dates)} rows, {dates[0]}..{dates[-1]}")

if __name__ == "__main__":
    main()
