"""Reverse proxy for Audiobookshelf and Calibre-Web.

Proxies /audiobookshelf/* → ABS_URL/* and /calibre/* → CALIBRE_URL/*
so the services don't need to be exposed publicly.
ABS is served at /audiobookshelf/ to match its configured base path.
Calibre-Web HTML is rewritten to prefix asset paths with /calibre/.
"""

import re

import httpx
from fastapi import APIRouter, Request, Response

from app.services import settings

router = APIRouter()

HOP_BY_HOP = frozenset({
    "host", "connection", "keep-alive", "transfer-encoding",
    "te", "trailers", "upgrade", "proxy-authorization",
    "proxy-authenticate", "content-encoding", "content-length",
})


def _filter_headers(headers, extra_strip=None):
    out = {}
    strip = HOP_BY_HOP | (extra_strip or set())
    for k, v in headers.items():
        if k.lower() not in strip:
            out[k] = v
    return out


async def _proxy(request: Request, base_url: str, path: str,
                 rewrite_html: bool = False, prefix: str = "") -> Response:
    url = f"{base_url.rstrip('/')}/{path}"
    qs = str(request.query_params)
    if qs:
        url += f"?{qs}"

    fwd_headers = _filter_headers(dict(request.headers))
    body = await request.body()

    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        upstream = await client.request(
            method=request.method,
            url=url,
            headers=fwd_headers,
            content=body if body else None,
        )

    resp_headers = _filter_headers(dict(upstream.headers))
    content = upstream.content

    # Rewrite HTML content to prefix internal paths
    if rewrite_html and prefix:
        ct = upstream.headers.get("content-type", "")
        if "text/html" in ct:
            html = content.decode("utf-8", errors="replace")
            # Prefix absolute paths: /static/, /login, /logout, etc.
            html = re.sub(
                r'((?:src|href|action)=["\'])/(?!calibre/|audiobookshelf/)',
                rf'\1/{prefix}/',
                html,
            )
            # Fix url() in inline styles
            html = html.replace("url('/static/", f"url('/{prefix}/static/")
            content = html.encode("utf-8")

    return Response(
        content=content,
        status_code=upstream.status_code,
        headers=resp_headers,
    )


# ABS uses base path /audiobookshelf/ — proxy at the same path so all
# internal asset references (/audiobookshelf/_nuxt/...) resolve correctly.
@router.api_route(
    "/audiobookshelf/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"],
)
async def proxy_abs(request: Request, path: str = ""):
    base = (settings.get("abs_url") or "http://audiobookshelf:80").rstrip("/")
    return await _proxy(request, base + "/audiobookshelf", path)


# Calibre-Web serves from / — proxy at /calibre/ with HTML rewriting
@router.api_route(
    "/calibre/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"],
)
async def proxy_calibre(request: Request, path: str = ""):
    base = (settings.get("calibre_url") or "http://calibre-web:8083").rstrip("/")
    return await _proxy(request, base, path, rewrite_html=True, prefix="calibre")
