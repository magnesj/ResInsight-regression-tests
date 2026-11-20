"""Exact pixel comparison of RegTestGeneratedImages against RegTestBaseImages.

Writes results.json and returns non-zero when any image differs or is missing.
For each differing image a binary diff (red = differing pixel) is written to
RegTestDiffImages, replacing the runner's diff image.Usage: python compare_results.py [--cases-dir cases] [--output results.json]
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def differing_pixels(base, generated):
    result = subprocess.run(
        ["compare", "-metric", "AE", str(base), str(generated), "null:"],
        capture_output=True,
        text=True,
    )
    # compare exits 1 for differing images, 2 for errors (e.g. size mismatch)
    if result.returncode == 2:
        return None
    return int(float(result.stderr.split()[0]))


def write_binary_diff(base, generated, output):
    """Write a black image where red pixels differ between the two images."""
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "convert", str(base), "-alpha", "off", str(generated), "-alpha", "off",
            "-compose", "difference", "-composite",
            "-separate", "-evaluate-sequence", "max",
            "-threshold", "0", "+level-colors", "black,red", str(output),
        ],
        check=True,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases-dir", default="cases", type=Path)
    parser.add_argument("--output", default="results.json", type=Path)
    args = parser.parse_args()

    results = []
    for case in sorted(args.cases_dir.glob("TestCase_*")):
        base_dir = case / "RegTestBaseImages"
        gen_dir = case / "RegTestGeneratedImages"
        generated = {p.name: p for p in gen_dir.glob("*.png")}
        base = {p.name: p for p in base_dir.glob("*.png")}
        for name in sorted(set(generated) | set(base)):
            if name not in generated:
                status, pixels = "missing_generated", None
            elif name not in base:
                status, pixels = "missing_base", None
            else:
                pixels = differing_pixels(base[name], generated[name])
                status = "pass" if pixels == 0 else "fail"
                if pixels:
                    write_binary_diff(
                        base[name], generated[name], case / "RegTestDiffImages" / name
                    )
            results.append(
                {"case": case.name, "image": name, "status": status, "pixels": pixels}
            )
        if not generated and not base:
            results.append(
                {"case": case.name, "image": None, "status": "no_images", "pixels": None}
            )

    args.output.write_text(json.dumps(results, indent=2) + "\n")
    failed = [r for r in results if r["status"] != "pass"]
    print(f"{len(results) - len(failed)} passed, {len(failed)} failed")
    for r in failed:
        print(f"  {r['status']}: {r['case']}/{r['image']} ({r['pixels']})")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
