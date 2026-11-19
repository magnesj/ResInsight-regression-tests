"""Store a nightly report under runs/<id>/ in the reports checkout and rebuild its index.

Runs older than 30 days are removed.

Usage: python archive_report.py --site reports --report report --results results.json
           --run-id <id> --sha <sha> --run-url <url> --outcome <success|failure>
"""

import argparse
import html
import json
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path


RETENTION_DAYS = 30


def prune(site, now):
    cutoff = f"{now - timedelta(days=RETENTION_DAYS):%Y-%m-%d}"
    for run_dir in (site / "runs").iterdir():
        # Run folders are named <date>-<run id>
        if run_dir.name[:10] < cutoff:
            shutil.rmtree(run_dir)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", default="reports", type=Path)
    parser.add_argument("--report", default="report", type=Path)
    parser.add_argument("--results", default="results.json", type=Path)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--run-url", default="")
    parser.add_argument("--outcome", default="")
    args = parser.parse_args()

    results = json.loads(args.results.read_text())
    now = datetime.now(timezone.utc)
    name = f"{now:%Y-%m-%d}-{args.run_id}"
    run_dir = args.site / "runs" / name
    shutil.rmtree(run_dir, ignore_errors=True)
    shutil.copytree(args.report, run_dir)

    passed = sum(1 for r in results if r["status"] == "pass")
    summary = {
        "name": name,
        "time": f"{now:%Y-%m-%d %H:%M UTC}",
        "sha": args.sha,
        "run_url": args.run_url,
        "outcome": args.outcome,
        "passed": passed,
        "total": len(results),
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")

    prune(args.site, now)
    summaries = []
    for path in (args.site / "runs").glob("*/summary.json"):
        summaries.append(json.loads(path.read_text()))
    summaries.sort(key=lambda s: s["name"], reverse=True)

    rows = []
    for s in summaries:
        color = "#2a9d4b" if s["passed"] == s["total"] else "#cc3333"
        sha = html.escape(s["sha"])
        run = f"<a href='{html.escape(s['run_url'])}'>run</a>" if s["run_url"] else ""
        rows.append(
            f"<tr><td><a href='runs/{html.escape(s['name'])}/index.html'>{html.escape(s['time'])}</a></td>"
            f"<td><a href='https://github.com/OPM/ResInsight/commit/{sha}'>{sha}</a></td>"
            f"<td style='color:{color}'>{s['passed']} / {s['total']} passed</td>"
            f"<td>{html.escape(s['outcome'])}</td><td>{run}</td></tr>"
        )
    latest = (
        f"<p>Latest report: <a href='runs/{summaries[0]['name']}/index.html'>"
        f"{html.escape(summaries[0]['time'])}</a></p>"
        if summaries
        else ""
    )
    page = (
        "<html><head><meta charset='utf-8'><style>body{font-family:sans-serif;margin:2em}"
        "td,th{padding:2px 12px;text-align:left}</style></head><body>"
        "<h1>ResInsight nightly regression</h1>"
        f"{latest}<table><tr><th>Time</th><th>Source</th><th>Result</th><th>Job</th><th></th></tr>"
        f"{''.join(rows)}</table></body></html>"
    )
    (args.site / "index.html").write_text(page, encoding="utf-8")


if __name__ == "__main__":
    main()
