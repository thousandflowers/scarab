import asyncio
from rich.progress import Progress, TextColumn, BarColumn, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn
from scarab.downloader.aria2_client import Aria2Client
from scarab.notifier.ntfy_client import NtfyClient
from scarab.config import global_config
import logging

logger = logging.getLogger(__name__)

async def handle_local_offload(url: str, filename: str, headers: dict, size_expected: int = None):
    # Retrieve configuration
    download_dir = global_config.get_local_downloads_dir()
    ntfy_server = global_config.get_ntfy_server()
    ntfy_topic = global_config.get_ntfy_topic()
    
    aria2 = Aria2Client()
    aria2.ensure_running(download_dir=download_dir)
    ntfy = NtfyClient(server=ntfy_server, topic=ntfy_topic)
    
    gid = aria2.add_download(url, filename=filename, headers=headers)
    logger.info(f"Avvio download locale per '{filename}' (GID: {gid}) in {download_dir}")
    
    with Progress(
        TextColumn("[bold blue]{task.fields[filename]}", justify="right"),
        BarColumn(bar_width=None),
        "[progress.percentage]{task.percentage:>3.1f}%",
        "•",
        DownloadColumn(),
        "•",
        TransferSpeedColumn(),
        "•",
        TimeRemainingColumn(),
        expand=True
    ) as progress:
        task_id = progress.add_task("download", filename=filename, total=size_expected or 100)
        
        while True:
            status = aria2.get_status(gid)
            if status["status"] == "complete":
                progress.update(task_id, completed=status["total_mb"], total=status["total_mb"])
                logger.info(f"Download locale completato: {filename}")
                ntfy.notify(
                    title="✅ Download completato",
                    message=f"Il file '{filename}' è stato salvato in {download_dir}.",
                    tags=["inbox_tray", "white_check_mark"]
                )
                break
            elif status["status"] in ["error", "removed", "paused"]:
                logger.error(f"Errore download {filename}: {status.get('error_message')}")
                ntfy.notify(
                    title="❌ Errore download",
                    message=f"Il download di '{filename}' è fallito.\nErrore: {status.get('error_message')}",
                    tags=["x", "warning"]
                )
                break
            
            # Progress update
            total = status.get("total_mb", size_expected or 100)
            completed = status.get("completed_mb", 0)
            if total > 0:
                progress.update(task_id, completed=completed, total=total)
            else:
                progress.update(task_id, completed=completed)
            
            await asyncio.sleep(2)
