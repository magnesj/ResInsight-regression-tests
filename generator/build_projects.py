"""Step 2: build cases/TestCase_<id>/RegressionTest.rsp from params.json using rips.

Requires the rips wheel matching the ResInsight binary and RESINSIGHT_EXECUTABLE.
The .rsp files embed absolute TestModels paths, so they are generated before each
run and are not committed.

Usage: python build_projects.py --testmodels <path to TestModels> [--cases <regex>]
"""

import argparse
import json
import re
from pathlib import Path

import rips

ROOT = Path(__file__).resolve().parent.parent


def build_case(resinsight, folder, testmodels):
    params = json.loads((folder / "params.json").read_text())["parameters"]
    project = resinsight.project
    project.close()

    case = project.load_case(str(testmodels / params["model"]))
    view = case.create_view()
    if params["result"] != "none":
        view.apply_cell_result("DYNAMIC_NATIVE", params["result"])
    view.show_grid_box = bool(params["grid_box"])
    view.update()

    project.save(str(folder / "RegressionTest.rsp"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--testmodels", required=True, type=Path)
    parser.add_argument("--cases", default=".*")
    args = parser.parse_args()

    testmodels = args.testmodels.resolve()
    pattern = re.compile(args.cases)
    folders = sorted(
        f for f in (ROOT / "cases").glob("TestCase_*") if pattern.search(f.name)
    )

    resinsight = rips.Instance.launch(console=True)
    try:
        for folder in folders:
            build_case(resinsight, folder, testmodels)
            print(f"built {folder.name}")
    finally:
        resinsight.exit()


if __name__ == "__main__":
    main()
