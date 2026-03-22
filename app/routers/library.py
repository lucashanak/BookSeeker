from fastapi import APIRouter, Depends, HTTPException
from app.services import auth, audiobookshelf

router = APIRouter(prefix="/api/library", tags=["library"])


@router.get("/status")
async def status(user: dict = Depends(auth.get_current_user)):
    return await audiobookshelf.get_status()


@router.get("/libraries")
async def libraries(user: dict = Depends(auth.get_current_user)):
    return await audiobookshelf.get_libraries()


@router.get("/libraries/{library_id}/items")
async def library_items(library_id: str, limit: int = 50, page: int = 0,
                        user: dict = Depends(auth.get_current_user)):
    return await audiobookshelf.get_library_items(library_id, limit=limit, page=page)


@router.get("/libraries/{library_id}/search")
async def search_library(library_id: str, q: str,
                         user: dict = Depends(auth.get_current_user)):
    results = await audiobookshelf.search_library(library_id, q)
    return {"results": results}


@router.get("/items/{item_id}")
async def get_item(item_id: str, user: dict = Depends(auth.get_current_user)):
    item = await audiobookshelf.get_item(item_id)
    if not item:
        raise HTTPException(404, "Item not found")
    return item


@router.get("/items/{item_id}/progress")
async def get_progress(item_id: str, user: dict = Depends(auth.get_current_user)):
    progress = await audiobookshelf.get_progress(item_id)
    return progress or {"progress": 0, "currentTime": 0, "isFinished": False}


@router.post("/libraries/{library_id}/scan")
async def scan_library(library_id: str, user: dict = Depends(auth.get_current_user)):
    ok = await audiobookshelf.scan_library(library_id)
    if not ok:
        raise HTTPException(500, "Scan failed")
    return {"status": "scanning"}
