"""FastAPI application — entry point, lifespan management, route mounting."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from server.config import FRONTEND_DIR
from server.database import run_migrations, backfill_partner_fields
from server.routes import campaigns, conversations, excluded, messages, metrics, settings, sync
from server.ws.handlers import router as ws_router
from server.ws.manager import manager
from server.services.salesmsg_client import SalesmsgClient
from server.services.sync_service import SyncService
from server.services.draft_service import DraftService

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: run migrations, start services. Shutdown: stop services."""
    # Startup
    run_migrations()
    backfill_partner_fields()

    client = SalesmsgClient()
    draft_svc = DraftService(ws_manager=manager)
    sync_svc = SyncService(
        salesmsg_client=client,
        ws_manager=manager,
        draft_service=draft_svc,
    )

    app.state.sync_service = sync_svc
    app.state.draft_service = draft_svc
    app.state.ws_manager = manager
    app.state.salesmsg_client = client

    await draft_svc.start()
    await sync_svc.start()

    logging.getLogger("main").info("All services started")

    yield

    # Shutdown
    await sync_svc.stop()
    await draft_svc.stop()
    await client.close()
    logging.getLogger("main").info("All services stopped")


app = FastAPI(title="Partner Outreach Dashboard", version="2.0.0", lifespan=lifespan)

# Mount API routes
app.include_router(campaigns.router)
app.include_router(conversations.router)
app.include_router(excluded.router)
app.include_router(messages.router)
app.include_router(metrics.router)
app.include_router(settings.router)
app.include_router(sync.router)

# Mount WebSocket BEFORE static files
app.include_router(ws_router)


@app.get("/api/health")
def health():
    """Health check with service status."""
    from server.database import get_db
    with get_db() as conn:
        convos = conn.execute("SELECT COUNT(*) FROM partner_conversations").fetchone()[0]
        msgs = conn.execute("SELECT COUNT(*) FROM message_log").fetchone()[0]
    return {
        "status": "ok",
        "conversations": convos,
        "messages": msgs,
        "ws_clients": manager.client_count,
    }


# Serve frontend static files
app.mount("/css", StaticFiles(directory=f"{FRONTEND_DIR}/css"), name="css")
app.mount("/js", StaticFiles(directory=f"{FRONTEND_DIR}/js"), name="js")
app.mount("/assets", StaticFiles(directory=f"{FRONTEND_DIR}/assets"), name="assets")


@app.get("/")
def serve_index():
    """Serve the main HTML page."""
    return FileResponse(f"{FRONTEND_DIR}/index.html")
