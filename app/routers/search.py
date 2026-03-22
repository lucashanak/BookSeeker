from fastapi import APIRouter, Depends
from app.services import auth, prowlarr

router = APIRouter(prefix="/api", tags=["search"])


@router.get("/search")
async def search(q: str, limit: int = 30, user: dict = Depends(auth.get_current_user)):
    results = await prowlarr.search(q, limit=limit)
    return {"results": results, "query": q}


@router.get("/indexers")
async def indexers(user: dict = Depends(auth.get_current_user)):
    return await prowlarr.get_indexers()
