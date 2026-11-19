"""Step 1: expand generator/config.yaml into cases/TestCase_<id>/params.json.

Needs only PyYAML. Run whenever config.yaml changes and commit the result.
Case folders that are no longer produced are removed.
"""

import json
import shutil
import sys
from pathlib import Path

import yaml

from pairwise import case_id, pairwise_cases

ROOT = Path(__file__).resolve().parent.parent


def main():
    config = yaml.safe_load((ROOT / "generator" / "config.yaml").read_text())
    cases = pairwise_cases(config["parameters"], config.get("exclude", []))

    cases_dir = ROOT / "cases"
    wanted = set()
    for case in cases:
        name = f"TestCase_{case_id(case)}"
        wanted.add(name)
        folder = cases_dir / name
        folder.mkdir(parents=True, exist_ok=True)
        params = {"snapshot": config["snapshot"], "parameters": case}
        (folder / "params.json").write_text(json.dumps(params, indent=2) + "\n")

    for folder in cases_dir.glob("TestCase_*"):
        if folder.name not in wanted:
            shutil.rmtree(folder)

    print(f"{len(wanted)} cases planned", file=sys.stderr)


if __name__ == "__main__":
    main()
