# Wiki Log

> Chronological record of wiki actions. Append-only.
> Format: `## [YYYY-MM-DD] action | subject`

## [2026-05-12] create | LLM Wiki initialized

- Created LLM Wiki root under `docs/llm-wiki/`.
- Added `SCHEMA.md`, `index.md`, and starter concept/source pages.
- Purpose: make data/pipeline decisions easy for teammates who are new to collaboration.

Changed files:

- `docs/llm-wiki/SCHEMA.md`
- `docs/llm-wiki/index.md`
- `docs/llm-wiki/log.md`

## [2026-05-12] ingest | Google Drive final folder inventory

- Source: <https://drive.google.com/drive/folders/1V-KJTNLjYpxqp_VAgIxKYQO6pm8-zMa2>
- Listed files with `gdown` in skip-download mode.
- Found 1,998 files: 779 PDF, 1,219 TXT.
- Saved manifest files under `data/manifests/`.

Changed files:

- `data/manifests/drive_inventory_2026-05-12.jsonl`
- `data/manifests/drive_inventory_2026-05-12.csv`
- `data/manifests/drive_inventory_2026-05-12.summary.json`
- `docs/llm-wiki/raw/sources/google-drive-final-folder-2026-05-12.md`

## [2026-05-12] data | raw PDF folder cleanup and smoke download

- Moved tracked root PDFs into `data/raw/pdfs/legacy-root/`.
- Created clean data folder skeleton with `.gitkeep` files.
- Downloaded G06F latest 10 smoke PDFs into `data/raw/pdfs/g06f/latest10/`.
- Added `.gitignore` rules so future bulk PDF/TXT/reports stay out of Git.
- Added smoke manifest and download script.

Changed files:

- `.gitignore`
- `data/README.md`
- `data/manifests/pilot_600_v1_smoke_g06f_latest10.jsonl`
- `scripts/data/download_smoke_pdfs.py`
- `docs/llm-wiki/concepts/pipeline-and-evaluation.md`
- `docs/llm-wiki/concepts/pilot-600-v1.md`

## [2026-05-12] update | BRANCH_RULES linked from collaboration docs

- Kept `BRANCH_RULES.md` at repository root.
- Linked it from `README.md` and [[team-collaboration-guide]].
- Clarified that the wiki collaboration guide extends branch rules with data/PDF safety rules.

Changed files:

- `README.md`
- `docs/llm-wiki/index.md`
- `docs/llm-wiki/concepts/team-collaboration-guide.md`

## [2026-05-12] update | early-stage wiki wording cleanup

- Clarified that actual user consultation data is not currently available and development will use simulated consultations.
- Removed large draft JSON examples for `patent_structure`, `simulated_consultation`, and pilot manifest fields.
- Left `invention_payload` example because it is tied to current code.
- Marked validation rules as TODO.
- Rewrote `SCHEMA.md` so it describes wiki rules, not a finalized product pipeline.
- Added beginner guide for teammates new to LLM Wiki.
- Added LangGraph/LangChain architecture notes as a non-final design memo.

Changed files:

- `docs/llm-wiki/README.md`
- `docs/llm-wiki/SCHEMA.md`
- `docs/llm-wiki/index.md`
- `docs/llm-wiki/concepts/data-management-strategy.md`
- `docs/llm-wiki/concepts/patent-data-schemas.md`
- `docs/llm-wiki/concepts/pipeline-and-evaluation.md`
- `docs/llm-wiki/concepts/pilot-600-v1.md`
- `docs/llm-wiki/concepts/llm-wiki-beginner-guide.md`
- `docs/llm-wiki/concepts/agent-architecture-notes.md`

## [2026-05-12] create | developer workflow scenario for teammates

- Added a scenario-style guide that explains how teammates should use LLM Wiki before, during, and after coding.
- Added example AI prompt for asking an AI coding assistant to follow the Wiki.
- Linked the scenario from README, index, beginner guide, and team collaboration guide.

Changed files:

- `docs/llm-wiki/README.md`
- `docs/llm-wiki/index.md`
- `docs/llm-wiki/concepts/developer-workflow-scenario.md`
- `docs/llm-wiki/concepts/team-collaboration-guide.md`
- `docs/llm-wiki/concepts/llm-wiki-beginner-guide.md`

## [2026-05-12] update | branch naming rule simplified

- Simplified `BRANCH_RULES.md` to focus only on branch naming.
- Adopted a generic personal integration branch style: `<name>`, then task branches like `<name>/docs/llm-wiki`, `<name>/data/pilot-manifest`, `<name>/feat/consultation-agent`.
- Removed the old feature branch after it had already been merged.
- Created a personal integration branch for ongoing work.

Changed files:

- `BRANCH_RULES.md`

## [2026-05-15] update | project structure and PR checklist synced

- Updated `BRANCH_RULES.md` so 은석, 가영, 범수, 서현, 홍익 each have their own confirmation checklist.
- Kept the PM checklist as the final confirmation checklist.
- Synced the LLM Wiki with the new folder structure: `agents/claim/`, `agents/drawing/`, `apps/streamlit/`, `notebooks/claim/`, `data/processed/claim_loop/training/`, `models/claim/`, and `docs/llm-wiki/schemas/`.
- Updated collaboration docs so folder-structure changes point back to `docs/PROJECT_STRUCTURE.md`.

Changed files:

- `BRANCH_RULES.md`
- `README.md`
- `docs/PROJECT_STRUCTURE.md`
- `docs/llm-wiki/README.md`
- `docs/llm-wiki/index.md`
- `docs/llm-wiki/log.md`
- `docs/llm-wiki/concepts/team-collaboration-guide.md`
- `docs/llm-wiki/concepts/developer-workflow-scenario.md`
- `docs/llm-wiki/concepts/data-management-strategy.md`
