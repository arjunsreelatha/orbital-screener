import subprocess
import sys
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

def run(cmd, desc):
    print(f"\n>>> {desc}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"FAILED: {desc}")
        sys.exit(1)
    print(f"OK: {desc}")

if __name__ == "__main__":
    # Step 1 — fetch TLEs
    run("python python/fetch_tles.py", "Fetching TLEs")

    # Step 2 — run C++ screener
    run("cpp\\build\\orbital_screener.exe", "Running conjunction screener")

    # Step 3 — build CDM records
    run("python python/build_cdm.py", "Building CDM records")

    # Step 4 — feature engineering
    run("python python/feature_engineering.py", "Feature engineering")

    # Step 5 — build dataset
    run("python python/build_dataset.py", "Building dataset CSV")

    print("\nPipeline complete. Starting FastAPI...")

    # Step 6 — start FastAPI (blocking)
    subprocess.run(
        "python -m uvicorn python.api.main:app --port 8000",
        shell=True
    )