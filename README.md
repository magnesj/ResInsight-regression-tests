# ResInsight regression tests

Nightly pixel-diff tests of ResInsight 3D views (2D plots are planned), using the
prebuilt `dev-latest` binary from `CeetronSolutions/resinsight-builds`, software
rendering (Mesa llvmpipe under xvfb) and exact (0 pixel) comparison.
See magnesj/ResInsight#1190.

## Layout

| Path | Content |
| --- | --- |
| `generator/features.py` | One function per rips feature; each builds a small project on the smallest suitable model |
| `generator/build_projects.py` | Runs every feature and writes `cases/TestCase_<feature>/RegressionTest.rsp` (generated, not committed) |
| `cases/TestCase_*/RegTestBaseImages/` | Reference images (Git LFS) |
| `scripts/` | Binary download, test run, exact compare, HTML report |
| `fonts/DroidSans.ttf` | Regression font picked up by ResInsight's runner |
| `.github/workflows/` | `nightly.yml`, `update-references.yml` |

Test models are not copied: the workflow does a sparse checkout of `TestModels/`
from `OPM/ResInsight` at the same SHA as the tested binary.

## Adding or changing cases

1. Add a function decorated with `@feature(name, model)` in `generator/features.py`. Each feature
   covers one rips capability once; do not repeat it on other grids.
2. Run the nightly workflow (`force`). A new feature has no references yet, so it is reported
   as `missing_base`. Promote it with the reference update workflow and review the image.

The case folder is `cases/TestCase_<feature>`. A feature that fails to build fails the run
(the other features still run).

## Running locally (Linux)

Needs `xvfb`, ImageMagick (`compare`), Mesa and `gh`.

```
scripts/fetch_binary.sh                       # downloads to bin/, prints source SHA
git clone --filter=blob:none --no-checkout https://github.com/OPM/ResInsight.git testmodels
(cd testmodels && git sparse-checkout set TestModels && git checkout <SHA>)
pip install bin/rips-*.whl
scripts/run_tests.sh [case-name-regex]
```

Results are in `results.json`, `run.log` and `cases/*/RegTestGeneratedImages`.
`python scripts/make_report.py --sha <SHA>` writes `report/index.html`.

## Nightly

`nightly.yml` runs at 03:30 UTC in a pinned `ubuntu:24.04` container, skips when the SHA of
`dev-latest` was already tested successfully (or `force`), caches the binary per SHA, uploads
report and generated images as an artifact, stores the report under `runs/` on the `reports` branch (reports older than 30 days are removed), publishes that branch to GitHub Pages and
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
