from pathlib import Path
import platform
import subprocess

PROJECT_ROOT = Path(__file__).resolve().parents[1]

def run_cpp():
    build_dir = PROJECT_ROOT / "cpp" / "build"

    exe = build_dir / (
        "orbital_screener.exe"
        if platform.system() == "Windows"
        else "orbital_screener"
    )

    if not exe.exists():
        raise FileNotFoundError(f"Executable not found: {exe}")

    subprocess.run([str(exe)], check=True)

if __name__ == "__main__":
    run_cpp()