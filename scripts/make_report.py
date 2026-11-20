"""Build a static HTML report from results.json.

Every case is listed with its feature description and model. Failing cases show
base / new / diff images, passing cases show the generated image.

Usage: python make_report.py --sha <sha> [--run-url <url>] [--output report]
"""

import argparse
import html
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

STYLE = """
body { font-family: sans-serif; margin: 2em; }
table.summary td, table.summary th { padding: 2px 10px; text-align: left; }
.case { border: 1px solid #ccc; border-radius: 4px; margin: 1em 0; padding: 0.5em 1em; }
.case h3 { margin: 0.2em 0; }
.meta { color: #555; font-size: 0.9em; }
.badge { padding: 1px 8px; border-radius: 10px; color: white; font-size: 0.85em; }
.pass { background: #2a9d4b; } .fail, .missing_generated, .no_images { background: #cc3333; }
.missing_base { background: #d08a00; }
.images { display: flex; gap: 1em; flex-wrap: wrap; }
.images figure { margin: 0; }
.images img { border: 1px solid #aaa; }
"""
CAPTIONS = {"diff": "diff (red = differing pixels)"}
ORDER = {"fail": 0, "missing_generated": 1, "no_images": 2, "missing_base": 3, "pass": 4}
IMAGE_FOLDERS = (
    ("base", "RegTestBaseImages"),
    ("new", "RegTestGeneratedImages"),
    ("diff", "RegTestDiffImages"),
)


def read_meta(cases_dir, case):
    path = cases_dir / case / "meta.json"
    return json.loads(path.read_text()) if path.is_file() else {}


def image_figures(result, cases_dir, output):
    shown = ("new",) if result["status"] == "pass" else ("base", "new", "diff")
    figures = []
    for label, folder in IMAGE_FOLDERS:
        if label not in shown or not result["image"]:
            continue
        src = cases_dir / result["case"] / folder / result["image"]
        if not src.is_file():
            figures.append(f"<figure><figcaption>{label}</figcaption>-</figure>")
            continue
        dest = output / f"{result['case']}_{label}_{result['image']}"
        shutil.copy(src, dest)
        name = html.escape(dest.name)
        figures.append(
            f"<figure><figcaption>{CAPTIONS.get(label, label)}</figcaption>"
            f"<a href='{name}'><img src='{name}' width='320'></a></figure>"
        )
    return "".join(figures)


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

    counts = {}
    for r in results:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    failed = len(results) - counts.get("pass", 0)

    cards = []
    for r in sorted(results, key=lambda r: (ORDER.get(r["status"], 9), r["case"])):
        meta = read_meta(args.cases_dir, r["case"])
        feature = r["case"].removeprefix("TestCase_")
        pixels = f" &middot; {r['pixels']} differing px" if r["pixels"] else ""
        cards.append(
            f"<div class='case' id='{html.escape(feature)}'>"
            f"<h3>{html.escape(feature)} "
            f"<span class='badge {r['status']}'>{r['status']}</span></h3>"
            f"<div>{html.escape(meta.get('description', ''))}</div>"
            f"<div class='meta'>Model: {html.escape(meta.get('model', '-'))} &middot; "
            f"image: {html.escape(str(r['image']))}{pixels}</div>"
            f"<div class='images'>{image_figures(r, args.cases_dir, args.output)}</div>"
            "</div>"
        )

    summary = "".join(
        f"<tr><th>{status}</th><td>{count}</td></tr>"
        for status, count in sorted(counts.items(), key=lambda i: ORDER.get(i[0], 9))
    )
    run = f" &middot; <a href='{html.escape(args.run_url)}'>source build run</a>" if args.run_url else ""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    sha = html.escape(args.sha)
    page = (
        f"<html><head><meta charset='utf-8'><style>{STYLE}</style></head><body>"
        "<p><a href='../../index.html'>&larr; All nightly reports</a></p>"
        "<h1>ResInsight nightly regression</h1>"
        f"<p>Source: <a href='https://github.com/OPM/ResInsight/commit/{sha}'>"
        f"OPM/ResInsight@{sha}</a>{run} &middot; generated {now}</p>"
        f"<p><b>{len(results) - failed} passed, {failed} not passing</b> "
        f"of {len(results)} images</p>"
        f"<table class='summary'>{summary}</table>"
        f"{''.join(cards)}</body></html>"
    )
    (args.output / "index.html").write_text(page, encoding="utf-8")


if __name__ == "__main__":
    main()
