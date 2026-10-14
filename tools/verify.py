"""Build and test both projects from any current working directory."""

from pathlib import Path
import shutil
import subprocess
import sys


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    node = shutil.which("node")
    if node is None:
        print("Node.js 22 or later is required; add node to PATH.", file=sys.stderr)
        return 1

    checks = (
        ("Build BreakGlassMap", [node, "scripts/build.mjs"], root / "BreakGlassMap"),
        ("Test BreakGlassMap", [node, "--test"], root / "BreakGlassMap"),
        ("Test CleanRoomCheck", [sys.executable, "-m", "unittest", "discover", "-v"], root / "CleanRoomCheck"),
        ("Test CleanRoomCheck UI", [node, "--test", "tests/ui.test.mjs"], root / "CleanRoomCheck"),
    )
    for label, command, directory in checks:
        print(f"\n{label}", flush=True)
        try:
            result = subprocess.run(command, cwd=directory, check=False)
        except OSError as error:
            print(f"{label}: {error}", file=sys.stderr)
            return 1
        if result.returncode:
            return result.returncode if result.returncode > 0 else 1
    print("\nBoth projects passed.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
