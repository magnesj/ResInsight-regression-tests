#!/usr/bin/env bash
# Download the dev-latest binary and rips wheel into ./bin and print the source SHA.
# Usage: scripts/fetch_binary.sh [release-tag]   (default dev-latest)
set -euo pipefail

TAG="${1:-dev-latest}"
REPO="CeetronSolutions/resinsight-builds"

mkdir -p bin
gh release download "$TAG" -R "$REPO" -p ResInsight-Ubuntu-26.zip -p rips.whl -D bin --clobber

# pip requires a canonical wheel filename: rename using the version in the wheel metadata.
ver=$(python3 -c "import re,zipfile;z=zipfile.ZipFile('bin/rips.whl');print(re.search(r'^Version: (\S+)',z.read([n for n in z.namelist() if n.endswith('METADATA')][0]).decode(),re.M).group(1))")
mv bin/rips.whl "bin/rips-${ver}-py3-none-any.whl"

sha=$(gh release view "$TAG" -R "$REPO" --json body -q .body | sed -n 's/^Built from OPM\/ResInsight@\([0-9a-f]*\).*/\1/p' | head -n1)
if [ -z "$sha" ]; then
  echo "Could not parse source SHA from release body" >&2
  exit 1
fi
echo "$sha" > bin/SOURCE_SHA

rm -rf bin/ResInsight
unzip -q bin/ResInsight-Ubuntu-26.zip -d bin/ResInsight
chmod +x bin/ResInsight/bin/ResInsight 2>/dev/null || true
echo "$sha"
