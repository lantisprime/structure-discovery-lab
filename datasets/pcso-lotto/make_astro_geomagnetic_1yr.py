"""
make_astro_geomagnetic_1yr.py
=============================================================
Generator for datasets/pcso-lotto/data_astro_geomagnetic_1yr.csv

Covers all 776 draws in data_draws_1yr.csv (2025-06-11 to 2026-06-10).

CONVENTIONS (replicated exactly from the existing data_astro_geomagnetic.csv):
  Observer: PCSO Main Office, Mandaluyong, Metro Manila
    lat = 14.5794 N, lon = 121.0359 E
  Draw time: 21:00 PHT = 13:00 UTC
  Library: PyEphem 4.2.1

TIDAL CONSTANTS (recovered empirically from existing file):
  C_moon = 2.998598e+11  (units: g * m^3)
    formula: lunar_tidal_accel_g = C_moon / d_moon_m^3
    derivation: C = 2 * G * M_moon * r / g0
      G = 6.674e-11, M_moon = 7.342e22 kg, g0 = 9.80665 m/s^2
      implies r = 0.300 m (reference height for tidal differential)
  C_sun = 8.121786e+18  (= C_moon * M_sun / M_moon)
    M_sun = 1.989e30 kg, M_moon = 7.342e22 kg

COLUMN ORDER (matches existing file exactly, plus 2 appended columns):
  Game, Draw Date, Moon Alt (deg), Moon Az (deg), Moon Illum (0-1),
  Moon Dist (km), Lunar tidal accel (g), Sun Alt (deg),
  Mean drawn # / pool, Kp at draw (geomagnetic), Kp daily mean,
  Sun Dist (km), Solar tidal accel (g)

KP CONVENTION:
  Kp at draw = 3-hourly bin containing 13:00 UTC = the 12:00-15:00 UTC bin
    (bin index 4 within a day, 0-indexed: 00,03,06,09,12,15,18,21)
  Kp daily mean = mean of all 8 bins for that day

POOL SIZES by game:
  Lotto 6/42 = 42, Mega Lotto 6/45 = 45, Super Lotto 6/49 = 49,
  Grand Lotto 6/55 = 55, Ultra Lotto 6/58 = 58

Usage:
  python3 make_astro_geomagnetic_1yr.py
Reads:
  data_draws_1yr.csv
  _kp_raw_1yr.json
Writes:
  data_astro_geomagnetic_1yr.csv

Generated: 2026-06-11
"""

import csv
import json
import math
import ephem
import os

# ── paths ──────────────────────────────────────────────────────────────────
HERE = os.path.dirname(os.path.abspath(__file__))
DRAWS_FILE = os.path.join(HERE, "data_draws_1yr.csv")
KP_FILE    = os.path.join(HERE, "_kp_raw_1yr.json")
OUT_FILE   = os.path.join(HERE, "data_astro_geomagnetic_1yr.csv")

# ── physical constants ──────────────────────────────────────────────────────
# Recovered from existing data_astro_geomagnetic.csv (mean over 194 rows)
C_MOON = 2.998598e+11   # g * m^3 for lunar tidal accel
C_SUN  = 8.121786e+18   # g * m^3 for solar tidal accel
# C_SUN = C_MOON * (M_sun / M_moon) = C_MOON * (1.989e30 / 7.342e22)
# Both C values correspond to reference height r = 0.300 m:
#   C = 2 * G * M / g0 * r  with G=6.674e-11, g0=9.80665

# ── pool sizes ──────────────────────────────────────────────────────────────
POOL = {
    "Lotto 6/42": 42,
    "Mega Lotto 6/45": 45,
    "Super Lotto 6/49": 49,
    "Grand Lotto 6/55": 55,
    "Ultra Lotto 6/58": 58,
}

# ── observer ────────────────────────────────────────────────────────────────
OBS = ephem.Observer()
OBS.lat  = "14.5794"
OBS.lon  = "121.0359"
OBS.elevation = 10       # Mandaluyong ~10m above sea level
OBS.pressure  = 1013     # standard atmosphere: enable refraction (matches existing file convention)

# ── load Kp data ────────────────────────────────────────────────────────────
def load_kp(kp_file):
    """Returns dict: date_str (YYYY-MM-DD) -> list of 8 Kp values (bins 00-21 UTC)."""
    with open(kp_file) as f:
        raw = json.load(f)
    dt_list = raw["datetime"]
    kp_list = raw["Kp"]
    assert len(dt_list) == len(kp_list), "Kp JSON length mismatch"

    day_kp = {}  # date -> list of (hour, kp)
    for dt_str, kp_val in zip(dt_list, kp_list):
        # dt_str like "2025-06-11T12:00:00Z"
        date_part = dt_str[:10]
        hour = int(dt_str[11:13])
        if date_part not in day_kp:
            day_kp[date_part] = {}
        day_kp[date_part][hour] = kp_val

    # Build: date -> sorted list of 8 values (hours 0,3,6,9,12,15,18,21)
    result = {}
    for date_str, hour_dict in day_kp.items():
        bins_ordered = [hour_dict.get(h) for h in [0,3,6,9,12,15,18,21]]
        result[date_str] = bins_ordered  # may contain None if missing
    return result


def get_kp_at_draw(kp_day, date_str):
    """Kp at draw = bin containing 13:00 UTC = 12:00-15:00 bin (index 4)."""
    bins = kp_day.get(date_str)
    if bins is None:
        return None, None
    kp_draw = bins[4]  # 12:00 UTC bin
    valid = [v for v in bins if v is not None]
    kp_mean = round(sum(valid) / len(valid), 3) if valid else None
    return kp_draw, kp_mean


def fmt_kp(val):
    """Format Kp value: strip trailing zeros like 2.667 stays 2.667, 2.0 -> 2."""
    if val is None:
        return ""
    # Match existing file format: integers shown without decimal, fractions shown as-is
    if val == int(val):
        return str(int(val))
    # Round to 3 decimal places
    s = f"{val:.3f}".rstrip("0")
    if s.endswith("."):
        s = s[:-1]
    return s


# ── ephemeris computation ────────────────────────────────────────────────────
def compute_ephemeris(date_str):
    """
    Compute moon & sun position at 13:00 UTC (= 21:00 PHT) for the given date.
    Returns dict with all needed values.
    """
    # Set observer time to 13:00 UTC
    obs = OBS.copy()
    obs.date = ephem.Date(f"{date_str} 13:00:00")

    moon = ephem.Moon(obs)
    sun  = ephem.Sun(obs)

    # Moon altitude and azimuth (radians -> degrees)
    moon_alt_deg = math.degrees(float(moon.alt))
    moon_az_deg  = math.degrees(float(moon.az))

    # Moon illumination fraction
    moon_illum = moon.phase / 100.0  # ephem gives percentage

    # Moon distance: moon.earth_distance is in AU; convert to km
    AU_KM = 149597870.7
    moon_dist_km = moon.earth_distance * AU_KM

    # Lunar tidal acceleration in g
    moon_dist_m = moon_dist_km * 1000.0
    lunar_tidal = C_MOON / (moon_dist_m ** 3)

    # Sun altitude (radians -> degrees)
    sun_alt_deg = math.degrees(float(sun.alt))

    # Sun distance in km
    sun_dist_km = sun.earth_distance * AU_KM

    # Solar tidal acceleration in g
    sun_dist_m = sun_dist_km * 1000.0
    solar_tidal = C_SUN / (sun_dist_m ** 3)

    return {
        "moon_alt": moon_alt_deg,
        "moon_az":  moon_az_deg,
        "moon_illum": moon_illum,
        "moon_dist_km": moon_dist_km,
        "lunar_tidal": lunar_tidal,
        "sun_alt": sun_alt_deg,
        "sun_dist_km": sun_dist_km,
        "solar_tidal": solar_tidal,
    }


def fmt_tidal(val):
    """Format tidal acceleration in 3 sig-fig e-notation, e.g. 4.41e-15."""
    # Use 3 significant figures
    s = f"{val:.2e}"
    return s


def fmt_solar_tidal(val):
    """Same convention as lunar tidal."""
    return f"{val:.2e}"


# ── main ─────────────────────────────────────────────────────────────────────
def main():
    print("Loading Kp data...")
    kp_day = load_kp(KP_FILE)
    print(f"  Kp coverage: {len(kp_day)} days")

    print("Reading draws...")
    draws = []
    with open(DRAWS_FILE) as f:
        reader = csv.DictReader(f)
        for row in reader:
            draws.append(row)
    print(f"  Draws: {len(draws)}")

    rows_out = []
    kp_missing_dates = []

    for row in draws:
        game      = row["Game"]
        date_str  = row["Date"]
        numbers   = [int(row[f"N{i}"]) for i in range(1, 7)]
        pool_size = POOL[game]

        # Ephemeris
        eph = compute_ephemeris(date_str)

        # Mean drawn number / pool
        mean_drawn = round(sum(numbers) / (6 * pool_size), 4)

        # Kp
        kp_draw, kp_mean = get_kp_at_draw(kp_day, date_str)
        if kp_draw is None:
            kp_missing_dates.append(date_str)

        rows_out.append({
            "Game":          game,
            "Draw Date":     date_str,
            "Moon Alt (deg)":  f"{eph['moon_alt']:.2f}",
            "Moon Az (deg)":   f"{eph['moon_az']:.1f}",
            "Moon Illum (0-1)":f"{eph['moon_illum']:.3f}",
            "Moon Dist (km)":  f"{int(round(eph['moon_dist_km']))}",
            "Lunar tidal accel (g)": fmt_tidal(eph["lunar_tidal"]),
            "Sun Alt (deg)":   f"{eph['sun_alt']:.2f}",
            "Mean drawn # / pool": f"{mean_drawn:.4f}",
            "Kp at draw (geomagnetic)": fmt_kp(kp_draw),
            "Kp daily mean":   fmt_kp(kp_mean),
            "Sun Dist (km)":   f"{int(round(eph['sun_dist_km']))}",
            "Solar tidal accel (g)": fmt_solar_tidal(eph["solar_tidal"]),
        })

    # Write output
    fieldnames = [
        "Game", "Draw Date",
        "Moon Alt (deg)", "Moon Az (deg)", "Moon Illum (0-1)",
        "Moon Dist (km)", "Lunar tidal accel (g)", "Sun Alt (deg)",
        "Mean drawn # / pool", "Kp at draw (geomagnetic)", "Kp daily mean",
        "Sun Dist (km)", "Solar tidal accel (g)",
    ]

    with open(OUT_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows_out)

    print(f"\nWrote {len(rows_out)} rows to {OUT_FILE}")

    if kp_missing_dates:
        print(f"WARNING: Kp missing for {len(kp_missing_dates)} dates:")
        for d in kp_missing_dates:
            print(f"  {d}")
    else:
        print("Kp coverage: complete (no missing dates)")

    return kp_missing_dates


if __name__ == "__main__":
    main()
