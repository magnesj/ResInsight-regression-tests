#!/usr/bin/env bash
# Run the regression tests with software rendering under xvfb.
# Usage: scripts/run_tests.sh [case-name-regex]   (requires scripts/fetch_binary.sh first)
set -euo pipefail

export LIBGL_ALWAYS_SOFTWARE=1
export RESINSIGHT_EXECUTABLE="$PWD/bin/ResInsight/ResInsight"
FILTER="${1:-}"

# Generated .rsp files embed absolute TestModels paths
python generator/build_projects.py --testmodels "$PWD/testmodels/TestModels" ${FILTER:+--cases "$FILTER"}

# The runner has no command line filter: run on a folder of symlinks to the selected
# cases. Images are written through the links into cases/.
rm -rf work
mkdir work
for d in cases/TestCase_*; do
  name=$(basename "$d")
  if [ -z "$FILTER" ] || [[ "$name" =~ $FILTER ]]; then
    ln -s "$PWD/$d" "work/$name"
  fi
done

xvfb-run -a "$RESINSIGHT_EXECUTABLE" --headless --regressiontest "$PWD/work" 2>&1 | tee run.log
grep -qi llvmpipe run.log || echo "::warning::llvmpipe not found in log, rendering may not be software"

# Exact-match gate is done separately so it does not depend on the built-in report
python scripts/compare_results.py --cases-dir work --output results.json
