"""
Entry point ASGI untuk Vercel (runtime Python / FastAPI).

Vercel memuat objek ``app`` dari file ini sebagai SATU-SATUNYA serverless
function untuk seluruh route project, sehingga frontend (React build) dan API
FastAPI berbagi satu domain/origin — tanpa memerlukan fitur "Services".

Kenapa begini?
    Pendekatan folder ``api/`` + mode static output (buildCommand +
    outputDirectory di vercel.json) ternyata TIDAK membuat function Python oleh
    Vercel → /api/* mengembalikan 404 meskipun frontend tampil. Solusinya:
    jadikan project sebagai satu aplikasi FastAPI (preset framework yang
    dideteksi Vercel lewat requirements.txt di root + file entrypoint ini),
    lalu FastAPI sendiri yang melayani seluruh request:
      - /api/*                -> route di backend/main.py (sumber kebenaran),
      - aset frontend (React) -> hasil build Vite di frontend/dist.

File ini hanya mengimpor ``app`` dari backend/main.py dan memasang middleware
untuk menyajikan file statis frontend di level produksi. Sumber kebenaran
endpoint tetap backend/main.py.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from main import app  # noqa: E402  (import setelah sys.path diubah, disengaja)

_FRONTEND_DIST = ROOT_DIR / "public"
if not _FRONTEND_DIST.is_dir():  # fallback untuk pengujian lokal (npm run build)
    _FRONTEND_DIST = ROOT_DIR / "frontend" / "dist"

if _FRONTEND_DIST.is_dir():
    from starlette.types import ASGIApp, Receive, Scope, Send

    class _FrontendStaticMiddleware:
        """Sajikan build React; minta /api/* diteruskan ke FastAPI.

        Diletakkan sebagai middleware (bukan route) supaya tidak bentrok dengan
        route ``/`` JSON yang didefinisikan di backend/main.py — middleware
        berjalan sebelum proses routing.
        """

        def __init__(self, app: ASGIApp, dist: Path) -> None:
            self.app = app
            self.dist = dist.resolve()
            self.index = dist / "index.html"
            # Path yang TETAP diteruskan ke FastAPI (bukan aset frontend).
            self.passthrough_prefixes = ("/api",)
            self.passthrough_exact = ("/docs", "/redoc", "/openapi.json")

        async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
            if scope["type"] != "http":
                await self.app(scope, receive, send)
                return

            path = scope["path"]
            if path.startswith(self.passthrough_prefixes) or path in self.passthrough_exact:
                await self.app(scope, receive, send)
                return

            from fastapi.responses import FileResponse

            candidate = (self.dist / path.lstrip("/")).resolve()
            try:
                candidate.relative_to(self.dist)
            except ValueError:
                candidate = self.index
            if not (candidate.is_file() and not path.endswith("/")):
                candidate = self.index
            response = FileResponse(candidate)
            await response(scope, receive, send)

    app.add_middleware(_FrontendStaticMiddleware, dist=_FRONTEND_DIST)

__all__ = ["app"]
