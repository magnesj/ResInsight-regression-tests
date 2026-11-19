"""Build a static HTML report (base / new / diff per image) from results.json.

Usage: python make_report.py --sha <sha> [--run-url <url>] [--output report]
"""

import argparse
import html
import json
import shutil
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sha", default="unknown")
    parser.add_argument("--run-url", default="")
    parser.add_argument("--results", default="results.json", type=Path)
    parser.add_argument("--cases-dir", default="cases", type=Path)
    parser.add_argument("--output", default="report", type=Path)
    args = parser.parse_args()

    results = json.loads(args.results.read_text())
    args.output.mkdir(exist_ok=True)
    failed = [r for r in results if r["status"] != "pass"]

    rows = []
    for r in failed:
        images = []
        for label, folder in (
            ("base", "RegTestBaseImages"),
            ("new", "RegTestGeneratedImages"),
            ("diff", "RegTestDiffImages"),
        ):
            src = args.cases_dir / r["case"] / folder / (r["image"] or "")
            if r["image"] and src.is_file():
                dest = args.output / f"{r['case']}_{label}_{r['image']}"
                shutil.copy(src, dest)
                images.append(
                    f"<td>{label}<br><img src='{html.escape(dest.name)}' width='320'></td>"
                )
            else:
                images.append(f"<td>{label}<br>-</td>")
        rows.append(
            f"<tr><td>{html.escape(r['case'])}<br>{html.escape(str(r['image']))}"
            f"<br>{r['status']} ({r['pixels']} px)</td>{''.join(images)}</tr>"
        )

    run = f"<a href='{html.escape(args.run_url)}'>source build run</a>" if args.run_url else ""
    page = (
        "<html><body><h1>ResInsight nightly regression</h1>"
        f"<p>Source: OPM/ResInsight@{html.escape(args.sha)} {run}</p>"
        f"<p>{len(results) - len(failed)} passed, {len(failed)} failed</p>"
        f"<table border='1'>{''.join(rows)}</table></body></html>"
    )
    (args.output / "index.html").write_text(page)


if __name__ == "__main__":
    main()
