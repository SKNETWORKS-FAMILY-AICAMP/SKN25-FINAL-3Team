"""Backward-compatible import shim.

The claim agent implementation lives in `agents/claim/claim_agent.py`.
Keep this file so older imports from the consultation Streamlit app or notebooks do not break.
"""

from pathlib import Path
import sys

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from agents.claim.claim_agent import *  # noqa: F401,F403
