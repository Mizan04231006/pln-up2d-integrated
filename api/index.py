"""
Vercel Python Serverless Function entrypoint.

Ini TIDAK menduplikasi logika backend — cuma mengimpor ulang objek FastAPI `app`
yang sudah ada di backend/main.py apa adanya, supaya satu-satunya sumber
kebenaran untuk endpoint tetap backend/main.py (dijalankan lokal via `uvicorn`
saat development, dan lewat file ini saat di-deploy ke Vercel).
"""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from main import app  # noqa: E402  (import setelah sys.path diubah, disengaja)

__all__ = ["app"]
