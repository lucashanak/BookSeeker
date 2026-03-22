from fastapi import APIRouter, Depends
from app.services import auth, prowlarr

router = APIRouter(prefix="/api", tags=["search"])


@router.get("/search")
async def search(q: str, type: str = "audiobook", limit: int = 30,
                 user: dict = Depends(auth.get_current_user)):
    if type == "ebook":
        category = prowlarr.CAT_BOOKS
        min_size = 0  # Ebooks can be very small
    else:
        category = prowlarr.CAT_AUDIO
        min_size = 50_000_000  # Audiobooks > 50MB
    results = await prowlarr.search(q, category=category, limit=limit, min_size=min_size)
    return {"results": results, "query": q, "type": type}


@router.get("/indexers")
async def indexers(user: dict = Depends(auth.get_current_user)):
    return await prowlarr.get_indexers()
