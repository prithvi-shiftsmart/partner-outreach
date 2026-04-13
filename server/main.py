"""FastAPI application — entry point, startup/shutdown, route mounting."""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from server.config import FRONTEND_DIR
from server.database import run_migrations, backfill_partner_fields
from server.routes import campaigns, conversations, excluded, messages, metrics, settings, sync

app = FastAPI(title="Partner Outreach Dashboard", version="2.0.0")

# Mount routes
app.include_router(campaigns.router)
app.include_router(conversations.router)
app.include_router(excluded.router)
app.include_router(messages.router)
app.include_router(metrics.router)
app.include_router(settings.router)
app.include_router(sync.router)


@app.on_event("startup")
def startup():
    run_migrations()
    backfill_partner_fields()


@app.get("/api/health")
def health():
    from server.database import get_db
    with get_db() as conn:
        convos = conn.execute("SELECT COUNT(*) FROM partner_conversations").fetchone()[0]
        msgs = conn.execute("SELECT COUNT(*) FROM message_log").fetchone()[0]
    return {"status": "ok", "conversations": convos, "messages": msgs}


# Serve frontend static files
app.mount("/css", StaticFiles(directory=f"{FRONTEND_DIR}/css"), name="css")
app.mount("/js", StaticFiles(directory=f"{FRONTEND_DIR}/js"), name="js")
app.mount("/assets", StaticFiles(directory=f"{FRONTEND_DIR}/assets"), name="assets")


@app.get("/")
def serve_index():
    return FileResponse(f"{FRONTEND_DIR}/index.html")
