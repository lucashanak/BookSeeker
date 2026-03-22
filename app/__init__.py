import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import APP_VERSION

def create_app() -> FastAPI:
    app = FastAPI(title="BookSeeker", version=APP_VERSION)

    from app.services import auth
    admin_user = os.environ.get("ADMIN_USER", "admin")
    admin_pass = os.environ.get("ADMIN_PASS", "")
    if admin_pass:
        auth.init_admin(admin_user, admin_pass)

    from app.routers import auth as auth_router
    from app.routers import search as search_router
    from app.routers import downloads as downloads_router
    from app.routers import library as library_router
    from app.routers import settings as settings_router
    from app.routers import ebooks as ebooks_router
    from app.routers import proxy as proxy_router

    app.include_router(auth_router.router)
    app.include_router(search_router.router)
    app.include_router(downloads_router.router)
    app.include_router(library_router.router)
    app.include_router(settings_router.router)
    app.include_router(ebooks_router.router)
    app.include_router(proxy_router.router)

    @app.get("/api/version")
    async def version():
        return {"version": APP_VERSION}

    static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/")
    async def index():
        return FileResponse(os.path.join(static_dir, "index.html"))

    return app
