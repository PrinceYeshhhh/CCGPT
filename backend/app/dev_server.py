"""
Robust development server entrypoint for CustomerCareGPT backend.

Features:
- Ensures project root is on PYTHONPATH to avoid ModuleNotFoundError for `app`.
- Loads local env files early (.env.local, .env, local.env).
- Automatically selects an available port starting from preferred one.
- Provides clear logging and CORS origin hinting for frontend.
"""

import os
import sys
import socket
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


def ensure_project_on_path() -> None:
    current_file = Path(__file__).resolve()
    backend_dir = current_file.parents[1]  # backend/
    project_root = backend_dir.parent      # project root
    # Add backend dir so `app` can be imported (package under backend/app)
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))
    # Also add project root for scripts that expect root context
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))


def load_env_files() -> None:
    backend_dir = Path(__file__).resolve().parents[1]
    for candidate in [backend_dir / ".env.local", backend_dir / ".env", backend_dir / "local.env"]:
        if candidate.exists():
            load_dotenv(dotenv_path=str(candidate), override=False)


def find_free_port(preferred: int) -> int:
    port = preferred
    for _ in range(20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                port += 1
    return preferred


def main() -> None:
    ensure_project_on_path()
    load_env_files()

    # Import after path/env are ready
    import uvicorn
    from app.core.config import settings

    preferred_port_env = os.getenv("PORT") or os.getenv("BACKEND_PORT")
    try:
        preferred_port = int(preferred_port_env) if preferred_port_env else 8000
    except ValueError:
        preferred_port = 8000

    port = find_free_port(preferred_port)

    if port != preferred_port:
        print(f"[dev_server] Preferred port {preferred_port} in use; selected free port {port}.")

    # Persist selected port for tooling/start scripts to consume
    try:
        backend_dir = Path(__file__).resolve().parents[1]
        port_file = backend_dir / ".backend_port"
        port_file.write_text(str(port), encoding="utf-8")
    except Exception as write_err:
        print(f"[dev_server] Warning: failed to write port file: {write_err}")

    # Helpful hints
    print("\nCustomerCareGPT Backend (dev) starting...")
    print(f"- Base URL: http://127.0.0.1:{port}")
    fe_hint = "http://127.0.0.1:5173"
    print(f"- If using Vite dev server, ensure CORS allows: {fe_hint}")
    print(f"- API v1 prefix: {settings.API_V1_PREFIX}")

    # Use import string to enable reload/workers correctly across platforms
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )


if __name__ == "__main__":
    main()


