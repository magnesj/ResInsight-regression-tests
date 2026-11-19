#!/usr/bin/env bash
# Download the dev-latest binary and rips wheel into ./bin and print the source SHA.
# Usage: scripts/fetch_binary.sh [release-tag]   (default dev-latest)
set -euo pipefail

TAG="${1:-dev-latest}"
REPO="CeetronSolutions/resinsight-builds"

mkdir -p bin
gh release download "$TAG" -R "$REPO" -p ResInsight-Ubuntu.zip -p rips.whl -D bin --clobber

sha=$(gh release view "$TAG" -R "$REPO" --json body -q .body | sed -n 's/^Built from OPM\/ResInsight@\([0-9a-f]*\).*/\1/p' | head -n1)
if [ -z "$sha" ]; then
  echo "Could not parse source SHA from release body" >&2
  exit 1
fi
echo "$sha" > bin/SOURCE_SHA

rm -rf bin/ResInsight
unzip -q bin/ResInsight-Ubuntu.zip -d bin/ResInsight
chmod +x bin/ResInsight/ResInsight 2>/dev/null || true
echo "$sha"
