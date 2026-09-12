"""API entry point. Run: python -m app.api.main [--debug]
Serves job submission/status. Probes here are what K8s liveness/readiness hit."""
import argparse

from fastapi import FastAPI

from app.api.routes import router
from app.shared import queue
from app.shared.db import init_db
from app.shared.logging_setup import setup_logging


def create_app(debug: bool = False) -> FastAPI:
    setup_logging(debug=debug, component="api")
    app = FastAPI(title="agent-conductor API")
    app.include_router(router)

    @app.on_event("startup")
    def _startup() -> None:
        init_db()  # create tables if absent

    # Liveness: process is up
    @app.get("/healthz")
    def healthz() -> dict:
        return {"status": "ok"}

    # Readiness: dependencies reachable (don't take traffic until Redis is up)
    @app.get("/readyz")
    def readyz() -> dict:
        return {"redis": queue.ping()}

    return app


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", help="enable debug logging")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    import uvicorn

    app = create_app(debug=args.debug)
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()