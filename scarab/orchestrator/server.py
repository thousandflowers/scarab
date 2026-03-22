import os
import shutil
import psutil
import asyncio
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from scarab.downloader.aria2_client import Aria2Client
from scarab.config import global_config
from scarab.notifier.ntfy_client import NtfyClient

logger = logging.getLogger(__name__)
app = FastAPI(title="Scarab Orchestrator")
aria2 = Aria2Client(secret=os.environ.get("ARIA2_SECRET", ""))
scheduler = AsyncIOScheduler()

# ─── Scheduler jobs ──────────────────────────────────────────────────────────

async def check_disk_space():
    """Sends a push notification if disk usage exceeds 90%."""
    total, used, _ = shutil.disk_usage("/")
    if total > 0 and (used / total) > 0.90:
        ntfy = NtfyClient(
            server=global_config.get_ntfy_server(),
            topic=global_config.get_ntfy_topic()
        )
        ntfy.notify(
            title="⚠️ Spazio disco critico",
            message="Lo spazio disco del nodo Server ha superato il 90%!",
            priority="high",
            tags=["warning", "cd"]
        )

# ─── Lifecycle ────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    scheduler.add_job(check_disk_space, "interval", minutes=60)
    scheduler.start()

@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown(wait=False)

# ─── Models ───────────────────────────────────────────────────────────────────

class JobRequest(BaseModel):
    url: str
    filename: Optional[str] = None
    headers: Optional[Dict[str, str]] = None

# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/api/status")
def get_status():
    download_dir = global_config.get_local_downloads_dir()
    os.makedirs(download_dir, exist_ok=True)
    total, used, free = shutil.disk_usage(download_dir)
    cpu_percent = psutil.cpu_percent(interval=0.1)
    
    active_downloads = 0
    try:
        aria2.ensure_running(download_dir)
        downloads = aria2.api.get_downloads()
        active_downloads = len([d for d in downloads if d.status == "active"])
    except Exception:
        pass  # aria2c might not be running yet

    return {
        "status": "online",
        "cpu_usage_percent": cpu_percent,
        "disk_free_mb": free / (1024 * 1024),
        "disk_total_mb": total / (1024 * 1024),
        "active_downloads": active_downloads
    }

async def notify_on_complete(gid: str, filename: str):
    """Background task: polls aria2 and sends a push notification when done."""
    ntfy = NtfyClient(
        server=global_config.get_ntfy_server(),
        topic=global_config.get_ntfy_topic()
    )
    while True:
        status = aria2.get_status(gid)
        if status["status"] == "complete":
            ntfy.notify(
                title="✅ Download remoto completato",
                message=f"Il file '{filename}' è stato salvato sul server.",
                tags=["cd", "white_check_mark"]
            )
            break
        elif status["status"] in ("error", "removed", "paused"):
            ntfy.notify(
                title="❌ Errore download remoto",
                message=f"Il download di '{filename}' è fallito: {status.get('error_message')}",
                tags=["x", "warning"]
            )
            break
        await asyncio.sleep(5)

@app.post("/api/jobs")
async def create_job(req: JobRequest):
    """Submits a new download job to aria2 and starts a completion watcher."""
    try:
        download_dir = global_config.get_local_downloads_dir()
        aria2.ensure_running(download_dir)
        gid = aria2.add_download(req.url, filename=req.filename, headers=req.headers)
        
        # asyncio.create_task works correctly inside an async route
        asyncio.create_task(
            notify_on_complete(gid, req.filename or req.url.split("/")[-1])
        )
        
        return {"job_id": gid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/jobs/{job_id}")
def get_job_status(job_id: str):
    return aria2.get_status(job_id)

@app.delete("/api/jobs/{job_id}")
def cancel_job(job_id: str):
    try:
        aria2.cancel(job_id)
        return {"status": "cancelled"}
    except Exception as e:
        raise HTTPException(status_code=404, detail="Job not found or already cancelled")
