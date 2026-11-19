# ResInsight regression tests

Nightly pixel-diff tests of ResInsight 3D views (2D plots are planned), using the
prebuilt `dev-latest` binary from `CeetronSolutions/resinsight-builds`, software
rendering (Mesa llvmpipe under xvfb) and exact (0 pixel) comparison.
See magnesj/ResInsight#1190.

## Layout

| Path | Content |
| --- | --- |
| `generator/config.yaml` | Parameter model and exclusion rules |
| `generator/plan.py` | Expands the model to pairwise cases: `cases/TestCase_<hash>/params.json` (committed) |
| `generator/build_projects.py` | Builds `RegressionTest.rsp` per case with `rips` (generated, not committed) |
| `cases/TestCase_*/RegTestBaseImages/` | Reference images (Git LFS) |
| `scripts/` | Binary download, test run, exact compare, HTML report |
| `fonts/DroidSans.ttf` | Regression font picked up by ResInsight's runner |
| `.github/workflows/` | `nightly.yml`, `update-references.yml` |

Test models are not copied: the workflow does a sparse checkout of `TestModels/`
from `OPM/ResInsight` at the same SHA as the tested binary.

## Adding or changing cases

1. Edit `generator/config.yaml` (add values or `exclude` rules).
2. `pip install pyyaml pytest && cd generator && python plan.py && python -m pytest`
3. Commit the changed `cases/*/params.json`. New cases have no references yet; the first
   nightly run reports `missing_base`. Promote them with the reference update workflow.

Case IDs are a hash of the parameters, so unchanged cases keep their folders and references.

## Running locally (Linux)

Needs `xvfb`, ImageMagick (`compare`), Mesa and `gh`.

```
scripts/fetch_binary.sh                       # downloads to bin/, prints source SHA
git clone --filter=blob:none --no-checkout https://github.com/OPM/ResInsight.git testmodels
(cd testmodels && git sparse-checkout set TestModels && git checkout <SHA>)
pip install bin/rips-*.whl pyyaml
scripts/run_tests.sh [case-name-regex]
```

Results are in `results.json`, `run.log` and `cases/*/RegTestGeneratedImages`.
`python scripts/make_report.py --sha <SHA>` writes `report/index.html`.

## Nightly

`nightly.yml` runs at 03:30 UTC in a pinned `ubuntu:24.04` container, skips when the SHA of
`dev-latest` was already tested successfully (or `force`), caches the binary per SHA, uploads
report and generated images as an artifact, publishes the report to GitHub Pages and
comments on the "Nightly regression" issue. The job fails when any image differs.

## Updating references

Run **Update references** (`workflow_dispatch`) with the nightly run ID and an optional case
name regex. It copies the generated images of that run into `RegTestBaseImages` and opens a
PR stating the producing SHA. Review the images in the nightly report before merging.

## Notes and known limits

- Exact matching requires a pinned Mesa. Changing the container image is a deliberate
  reference refresh.
- Settings required to be set: Git LFS for `*.png`; repository secret `DEV_BUILDS_READ_TOKEN`
  is only needed if `resinsight-builds` is not publicly readable.
- Not yet done: 2D plots, more parameters (filters, faults, wells, time step, camera), a
  double run to detect flaky cases, sharding across jobs. Verify that the published Ubuntu
  zip runs on a clean container (library list in `nightly.yml` is a first guess).
