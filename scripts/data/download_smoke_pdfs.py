#!/usr/bin/env python3
"""Download only the selected smoke-set PDFs from a manifest.

Usage:
    uv run --with gdown python scripts/data/download_smoke_pdfs.py \
      --manifest data/manifests/pilot_600_v1_smoke_g06f_latest10.jsonl
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import gdown


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="data/manifests/pilot_600_v1_smoke_g06f_latest10.jsonl")
    parser.add_argument("--skip-existing", action="store_true", default=True)
    args = parser.parse_args()

    manifest = Path(args.manifest)
    rows = [json.loads(line) for line in manifest.read_text(encoding="utf-8").splitlines() if line.strip()]

    downloaded = 0
    skipped = 0
    for row in rows:
        output = Path(row["local_pdf_path"])
        output.parent.mkdir(parents=True, exist_ok=True)
        if args.skip_existing and output.exists() and output.stat().st_size > 0:
            skipped += 1
            print(f"SKIP existing: {output}")
            continue
        print(f"DOWNLOAD {row['drive_path']} -> {output}")
        gdown.download(id=row["drive_file_id"], output=str(output), quiet=False, use_cookies=False)
        downloaded += 1

    print(json.dumps({"manifest": str(manifest), "downloaded": downloaded, "skipped": skipped}, ensure_ascii=False))


if __name__ == "__main__":
    main()
