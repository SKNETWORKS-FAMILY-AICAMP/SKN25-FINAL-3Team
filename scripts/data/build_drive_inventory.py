#!/usr/bin/env python3
"""Build a Google Drive inventory manifest without downloading files.

Usage:
    uv run --with gdown python scripts/data/build_drive_inventory.py
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import io
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path

import gdown

DEFAULT_FOLDER_URL = "https://drive.google.com/drive/folders/1V-KJTNLjYpxqp_VAgIxKYQO6pm8-zMa2"


def infer_ipc(path: str) -> str:
    for part in Path(path).parts:
        if re.fullmatch(r"G\d{2}[A-Z]?", part):
            return part
    return ""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder-url", default=DEFAULT_FOLDER_URL)
    parser.add_argument("--output-dir", default="data/manifests")
    parser.add_argument("--date", default=date.today().isoformat())
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # gdown prints every discovered file even in skip-download mode. Capture that noise.
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        items = gdown.download_folder(
            url=args.folder_url,
            output="/tmp/drive_inventory_probe",
            quiet=True,
            skip_download=True,
            use_cookies=False,
        )

    rows = []
    for item in items or []:
        drive_path = item.path
        file_name = Path(drive_path).name
        extension = Path(file_name).suffix.lower().lstrip(".") or "no_ext"
        patent_id_guess = re.sub(r"_extracted$", "", Path(file_name).stem)
        top_folder = Path(drive_path).parts[0] if Path(drive_path).parts else ""
        rows.append(
            {
                "drive_file_id": item.id,
                "drive_path": drive_path,
                "file_name": file_name,
                "extension": extension,
                "top_folder": top_folder,
                "ipc_folder": infer_ipc(drive_path),
                "patent_id_guess": patent_id_guess,
                "source_url": f"https://drive.google.com/file/d/{item.id}/view",
            }
        )

    stem = f"drive_inventory_{args.date}"
    jsonl_path = output_dir / f"{stem}.jsonl"
    csv_path = output_dir / f"{stem}.csv"
    summary_path = output_dir / f"{stem}.summary.json"

    with jsonl_path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    if rows:
        with csv_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

    summary = {
        "source_folder_url": args.folder_url,
        "total_files": len(rows),
        "by_extension": dict(Counter(row["extension"] for row in rows).most_common()),
        "by_top_folder": dict(Counter(row["top_folder"] for row in rows).most_common()),
        "by_ipc_folder": dict(Counter(row["ipc_folder"] or "(none)" for row in rows).most_common()),
        "sample_paths": [row["drive_path"] for row in rows[:20]],
        "manifest_jsonl": str(jsonl_path),
        "manifest_csv": str(csv_path),
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
