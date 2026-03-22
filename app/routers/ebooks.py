import os
import mimetypes
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from app.services import auth
from app.config import EBOOK_DIR

router = APIRouter(prefix="/api/ebooks", tags=["ebooks"])

EBOOK_EXTENSIONS = {".epub", ".pdf", ".mobi", ".azw3", ".azw", ".fb2", ".djvu", ".cbr", ".cbz", ".txt"}


@router.get("/files")
async def list_files(path: str = "", user: dict = Depends(auth.get_current_user)):
    """List files and folders in the ebook directory."""
    base = os.path.realpath(EBOOK_DIR)
    target = os.path.realpath(os.path.join(base, path))
    # Prevent path traversal
    if not target.startswith(base):
        raise HTTPException(400, "Invalid path")
    if not os.path.isdir(target):
        raise HTTPException(404, "Directory not found")

    items = []
    try:
        for entry in sorted(os.scandir(target), key=lambda e: (not e.is_dir(), e.name.lower())):
            if entry.name.startswith("."):
                continue
            rel_path = os.path.relpath(entry.path, base)
            if entry.is_dir():
                # Count ebook files in dir
                ebook_count = 0
                total_size = 0
                for dp, _, fns in os.walk(entry.path):
                    for f in fns:
                        ext = os.path.splitext(f)[1].lower()
                        if ext in EBOOK_EXTENSIONS:
                            ebook_count += 1
                            try:
                                total_size += os.path.getsize(os.path.join(dp, f))
                            except OSError:
                                pass
                items.append({
                    "name": entry.name,
                    "path": rel_path,
                    "is_dir": True,
                    "ebook_count": ebook_count,
                    "size": total_size,
                })
            else:
                ext = os.path.splitext(entry.name)[1].lower()
                items.append({
                    "name": entry.name,
                    "path": rel_path,
                    "is_dir": False,
                    "is_ebook": ext in EBOOK_EXTENSIONS,
                    "ext": ext.lstrip("."),
                    "size": entry.stat().st_size,
                })
    except PermissionError:
        raise HTTPException(403, "Permission denied")

    return {"items": items, "path": path, "base_dir": EBOOK_DIR}


@router.get("/download/{file_path:path}")
async def download_file(file_path: str, user: dict = Depends(auth.get_current_user)):
    """Download an ebook file."""
    base = os.path.realpath(EBOOK_DIR)
    target = os.path.realpath(os.path.join(base, file_path))
    if not target.startswith(base):
        raise HTTPException(400, "Invalid path")
    if not os.path.isfile(target):
        raise HTTPException(404, "File not found")

    mime_type = mimetypes.guess_type(target)[0] or "application/octet-stream"
    return FileResponse(
        target,
        media_type=mime_type,
        filename=os.path.basename(target),
        headers={"Content-Disposition": f'attachment; filename="{os.path.basename(target)}"'},
    )
