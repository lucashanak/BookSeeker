"""Prowlarr API client — search torrent indexers."""
import httpx

from app.config import PROWLARR_URL, PROWLARR_API_KEY

# Prowlarr categories
CAT_AUDIO = "3000"
CAT_BOOKS = "7000"


async def search(query: str, category: str = CAT_AUDIO, limit: int = 30,
                 min_size: int = 0) -> list[dict]:
    """Search Prowlarr for torrents in given category."""
    if not PROWLARR_API_KEY:
        return []
    params = {
        "query": query,
        "categories": category,
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
    for item in raw[:limit * 2]:
        size = item.get("size", 0)
        if min_size and size < min_size:
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
    results.sort(key=lambda x: x["seeders"], reverse=True)
    return results[:limit]


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
