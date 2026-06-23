from sgp4.api import Satrec,jday
from pathlib import Path
from datetime import datetime, timezone

TLE_PATH = Path(__file__).resolve().parents[1] / "data" / "tles" / "starlink.tle"

def load_first_tle(path):
    lines = [l.strip() for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    name = lines[0]
    line1 = lines[1]
    line2 = lines[2]
    return name, line1, line2

def propagate(line1, line2, dt):
    sat = Satrec.twoline2rv(line1, line2)
    jd, fr = jday(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second + dt.microsecond/1e6)
    e, r, v = sat.sgp4(jd, fr)
    return e, r, v

if __name__ == "__main__":
    name, line1, line2 = load_first_tle(TLE_PATH)
    print(f"Satellite: {name}")
    print(f"Line1: {line1}")
    print(f"Line2: {line2}")

    now = datetime.now(timezone.utc)
    print(f"\nPropagating to: {now.isoformat()}")

    e, r, v = propagate(line1, line2, now)

    if e != 0:
        print(f"SGP4 error code: {e}")
    else:
        print(f"\nPosition (TEME, km):")
        print(f"  x = {r[0]:.3f}")
        print(f"  y = {r[1]:.3f}")
        print(f"  z = {r[2]:.3f}")
        print(f"\nVelocity (TEME, km/s):")
        print(f"  vx = {v[0]:.6f}")
        print(f"  vy = {v[1]:.6f}")
        print(f"  vz = {v[2]:.6f}")