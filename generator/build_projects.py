"""Build cases/TestCase_<feature>/RegressionTest.rsp for every feature in features.py.

Requires the rips wheel matching the ResInsight binary and RESINSIGHT_EXECUTABLE.
The .rsp files embed absolute TestModels paths, so they are generated before each
run and are not committed.

Usage: python build_projects.py --testmodels <path to TestModels> [--cases <regex>]
"""

import argparse
import json
import re
import sys
import traceback
from pathlib import Path

import rips

from features import FEATURES

ROOT = Path(__file__).resolve().parent.parent


def build_case(resinsight, name, testmodels):
    build, model = FEATURES[name]
    folder = ROOT / "cases" / f"TestCase_{name}"
    folder.mkdir(parents=True, exist_ok=True)
    rsp = folder / "RegressionTest.rsp"
    rsp.unlink(missing_ok=True)
    description = (build.__doc__ or "").strip()
    meta = {"description": description, "model": model}
    (folder / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")

    project = resinsight.project
    project.close()
    case = project.load_case(str(testmodels / model))
    view = case.create_view()
    build(project, case, view, testmodels)
    project.save(str(rsp))
    _enable_time_axis_auto_zoom(rsp)


def _enable_time_axis_auto_zoom(rsp: Path):
    """The hidden plot widget turns off auto zoom of the time axis while laying out the plot, which saves an
    empty time range and gives plots without time axis and curves. Restore auto zoom in the saved project."""
    text = rsp.read_text()
    fixed = re.sub(
        r"(<SummaryTimeAxisProperties>.*?<AutoZoom>)False( ?</AutoZoom>)",
        r"\1True\2",
        text,
        flags=re.DOTALL,
    )
    if fixed != text:
        rsp.write_text(fixed)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--testmodels", required=True, type=Path)
    parser.add_argument("--cases", default=".*")
    args = parser.parse_args()

    testmodels = args.testmodels.resolve()
    pattern = re.compile(args.cases)
    names = sorted(n for n in FEATURES if pattern.search(f"TestCase_{n}"))

    failed = []
    resinsight = rips.Instance.launch(console=True)
    try:
        for name in names:
            try:
                build_case(resinsight, name, testmodels)
                print(f"built {name}")
            except Exception:
                failed.append(name)
                print(f"FAILED to build {name}", file=sys.stderr)
                traceback.print_exc()
    finally:
        resinsight.exit()

    if failed:
        print(f"::error::Could not build features: {', '.join(failed)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
