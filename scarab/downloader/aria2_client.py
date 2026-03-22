# scarab/downloader/aria2_client.py
import httpx
import asyncio
from dataclasses import dataclass
from enum import Enum
from scarab.setup.dependencies import get_aria2_token, ARIA2_DOWNLOADS

ARIA2_RPC = "http://localhost:6800/jsonrpc"

class JobStatus(Enum):
    QUEUED      = "waiting"
    DOWNLOADING = "active"
    COMPLETE    = "complete"
    ERROR       = "error"
    PAUSED      = "paused"

@dataclass
class DownloadJob:
    gid: str
    filename: str
    status: JobStatus
    progress_pct: float
    speed_mbps: float
    total_bytes: int
    completed_bytes: int

def _rpc(method: str, params: list) -> dict:
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "id": "scarab",
        "params": [f"token:{get_aria2_token()}"] + params
    }
    try:
        r = httpx.post(ARIA2_RPC, json=payload, timeout=10)
        r.raise_for_status()
        data = r.json()
        if "error" in data:
            raise RuntimeError(f"aria2: {data['error']['message']}")
        return data.get("result")
    except httpx.ConnectError:
        raise RuntimeError(
            "aria2 is not responding. "
            "Run 'scarab start' to launch Scarab."
        )

def add_download(url: str, filename: str = None) -> str:
    """Adds a download to aria2. Returns the GID."""
    options = {"dir": str(ARIA2_DOWNLOADS)}
    if filename:
        options["out"] = filename
    return _rpc("aria2.addUri", [[url], options])

def get_job_status(gid: str) -> DownloadJob:
    keys = ["gid", "status", "totalLength",
            "completedLength", "downloadSpeed", "files"]
    r = _rpc("aria2.tellStatus", [gid, keys])

    total     = int(r.get("totalLength", 0))
    completed = int(r.get("completedLength", 0))
    speed     = int(r.get("downloadSpeed", 0))
    progress  = (completed / total * 100) if total > 0 else 0.0
    files     = r.get("files", [{}])
    path      = files[0].get("path", "") if files else ""
    filename  = path.split("/")[-1] if path else "file"

    return DownloadJob(
        gid=gid,
        filename=filename,
        status=JobStatus(r.get("status", "waiting")),
        progress_pct=round(progress, 1),
        speed_mbps=round(speed / 1_000_000, 2),
        total_bytes=total,
        completed_bytes=completed,
    )

def cancel_download(gid: str) -> bool:
    try:
        _rpc("aria2.remove", [gid])
        return True
    except Exception:
        return False

async def wait_for_completion(gid: str, on_progress=None) -> DownloadJob:
    """
    Polls until the download completes or fails.
    Calls on_progress(job) every 2 seconds if provided.
    """
    while True:
        job = get_job_status(gid)
        if on_progress:
            on_progress(job)
        if job.status == JobStatus.COMPLETE:
            return job
        if job.status == JobStatus.ERROR:
            raise RuntimeError(f"Download failed: {job.filename}")
        await asyncio.sleep(2)
