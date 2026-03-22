from fastapi import APIRouter, Depends
from app.services import auth
from app.config import PROWLARR_URL, PROWLARR_API_KEY, QBIT_URL, ABS_URL

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("")
async def get_settings(user: dict = Depends(auth.get_current_user)):
    return {
        "prowlarr_url": PROWLARR_URL,
        "prowlarr_connected": bool(PROWLARR_API_KEY),
        "qbit_url": QBIT_URL,
        "abs_url": ABS_URL,
    }
