"""Prowlarr API client — search torrent indexers for audiobooks."""
import httpx

from app.config import PROWLARR_URL, PROWLARR_API_KEY


async def search(query: str, limit: int = 30) -> list[dict]:
    """Search Prowlarr for audiobooks (category 3000=Audio)."""
    if not PROWLARR_API_KEY:
        return []
    params = {
        "query": query,
        "categories": "3000",
        "type": "search",
        "apikey": PROWLARR_API_KEY,
    }
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(f"{PROWLARR_URL}/api/v1/search", params=params)
            resp.raise_for_status()
            raw = resp.json()
    except Exception:
        return []

    results = []
    for item in raw[:limit]:
        size = item.get("size", 0)
        # Skip tiny results (< 50MB, likely not audiobooks)
        if size < 50_000_000:
            continue
        cats = [c.get("id", 0) for c in item.get("categories", [])]
        results.append({
            "title": item.get("title", ""),
            "indexer": item.get("indexer", ""),
            "size": size,
            "seeders": item.get("seeders", 0),
            "leechers": item.get("leechers", 0),
            "download_url": item.get("downloadUrl", ""),
            "magnet_url": item.get("magnetUrl", ""),
            "info_url": item.get("infoUrl", ""),
            "categories": cats,
            "age_days": item.get("age", 0),
            "grabs": item.get("grabs", 0),
        })
    # Sort: more seeders first
    results.sort(key=lambda x: x["seeders"], reverse=True)
    return results


async def get_indexers() -> list[dict]:
    """List configured Prowlarr indexers."""
    if not PROWLARR_API_KEY:
        return []
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{PROWLARR_URL}/api/v1/indexer",
                params={"apikey": PROWLARR_API_KEY},
            )
            resp.raise_for_status()
            return [
                {"id": i["id"], "name": i["name"], "enabled": i["enable"]}
                for i in resp.json()
            ]
    except Exception:
        return []
