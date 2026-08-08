from fetch_tles import fetch_tles
from run_cpp import run_cpp
from build_cdm import build_cdm
from feature_engineering import feature_engineering
from build_dataset import build_dataset


def refresh_pipeline():
    print("========== Orbital Screener Pipeline ==========")

    print("[1/5] Fetching latest TLEs...")
    fetch_tles()

    print("[2/5] Running orbital propagation...")
    run_cpp()

    print("[3/5] Building CDM records...")
    build_cdm()

    print("[4/5] Running feature engineering...")
    feature_engineering()

    print("[5/5] Building dataset...")
    build_dataset()

    print("Pipeline completed successfully.")


if __name__ == "__main__":
    refresh_pipeline()