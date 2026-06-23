from pathlib import Path
import time
import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = PROJECT_ROOT / "data" / "tles" / "starlink.tle"
CACHE_HOURS = 24
URL = "https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=tle"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
}


def fetch_tles():
    if OUTPUT_PATH.exists():
        age_hours = (time.time() - OUTPUT_PATH.stat().st_mtime) / 3600
        if age_hours < CACHE_HOURS:
            print(f"Using cached TLEs (age: {age_hours:.1f} hours)")
            lines = [line.strip() for line in OUTPUT_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
            print(f"Total lines: {len(lines)}")
            print(f"Approx objects: {len(lines) // 3}")
            return

    print("Fetching TLEs from CelesTrak...")

    try:
        response = requests.get(URL, headers=HEADERS, timeout=30)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code == 403:
            print("403 Forbidden from CelesTrak.")
            print("This usually means the TLE endpoint is blocked or unavailable for this group.")
            print("Keep using JSON/OMM for Starlink, or switch to a smaller TLE-friendly group for propagation testing.")
            return
        raise

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(response.text, encoding="utf-8")

    lines = [line.strip() for line in response.text.splitlines() if line.strip()]
    print(f"Saved TLE data to {OUTPUT_PATH}")
    print(f"Total lines: {len(lines)}")
    print(f"Approx objects: {len(lines) // 3}")


if __name__ == "__main__":
    fetch_tles()