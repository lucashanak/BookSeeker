"""Reverse proxy for Audiobookshelf and Calibre-Web.

Proxies /audiobookshelf/* → ABS_URL/* and /calibre/* → CALIBRE_URL/*
so the services don't need to be exposed publicly.
ABS is served at /audiobookshelf/ to match its configured base path.
ABS auto-login: JS injected into the HTML waits for the login form
to render, fills credentials, and clicks Submit automatically.
Calibre-Web HTML is rewritten to prefix asset paths with /calibre/.
"""

import re

import httpx
from fastapi import APIRouter, Request, Response

from app.services import settings
from app.config import ABS_URL, ABS_USER, ABS_PASS, CALIBRE_USER, CALIBRE_PASS

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

    async with httpx.AsyncClient(timeout=30, follow_redirects=False) as client:
        upstream = await client.request(
            method=request.method,
            url=url,
            headers=fwd_headers,
            content=body if body else None,
        )

    resp_headers = _filter_headers(dict(upstream.headers))

    # Rewrite redirect Location headers to include the proxy prefix
    if prefix and "location" in resp_headers:
        loc = resp_headers["location"]
        if loc.startswith("/") and not loc.startswith(f"/{prefix}/"):
            resp_headers["location"] = f"/{prefix}{loc}"

    # Pass through Set-Cookie headers (multi-value)
    set_cookies = upstream.headers.get_list("set-cookie")

    content = upstream.content

    if rewrite_html and prefix:
        ct = upstream.headers.get("content-type", "")
        if "text/html" in ct:
            html = content.decode("utf-8", errors="replace")
            html = re.sub(
                r'((?:src|href|action)=["\'])/(?!calibre/|audiobookshelf/)',
                rf'\1/{prefix}/',
                html,
            )
            html = html.replace("url('/static/", f"url('/{prefix}/static/")
            content = html.encode("utf-8")

    resp = Response(
        content=content,
        status_code=upstream.status_code,
        headers=resp_headers,
    )
    # Append all Set-Cookie headers (Response dict drops duplicates)
    for cookie in set_cookies:
        resp.headers.append("set-cookie", cookie)
    return resp


def _abs_autologin_script() -> str:
    """JS that waits for the ABS login form and auto-submits credentials."""
    user = settings.get("abs_user") or ABS_USER or ""
    pwd = settings.get("abs_pass") or ABS_PASS or ""
    # Escape backslashes and quotes for JS string safety
    user_js = user.replace("\\", "\\\\").replace('"', '\\"')
    pwd_js = pwd.replace("\\", "\\\\").replace('"', '\\"')
    return f'''<script>
(function() {{
  if (sessionStorage.getItem("_abs_autologin")) return;
  var tries = 0;
  var timer = setInterval(function() {{
    tries++;
    if (tries > 50) {{ clearInterval(timer); return; }}
    // Target password input specifically to find the login form
    var pInput = document.querySelector('input[type="password"]');
    if (!pInput) return;
    // Username input is the text input right before password
    var uInput = pInput.parentElement.querySelector('input[type="text"]')
      || pInput.closest('div').parentElement.querySelector('input[type="text"]');
    // Find Submit button near the form
    var btn = null;
    var btns = document.querySelectorAll('button');
    for (var i = 0; i < btns.length; i++) {{
      if (btns[i].textContent.trim().toLowerCase() === 'submit') {{
        btn = btns[i]; break;
      }}
    }}
    if (uInput && pInput && btn) {{
      clearInterval(timer);
      // Set values via native setter to trigger Vue reactivity
      var nSet = Object.getOwnPropertyDescriptor(
        HTMLInputElement.prototype, 'value'
      ).set;
      nSet.call(uInput, "{user_js}");
      uInput.dispatchEvent(new Event('input', {{bubbles: true}}));
      nSet.call(pInput, "{pwd_js}");
      pInput.dispatchEvent(new Event('input', {{bubbles: true}}));
      sessionStorage.setItem("_abs_autologin", "1");
      setTimeout(function() {{ btn.click(); }}, 100);
    }}
  }}, 200);
}})();
</script>'''


# ABS proxy — auto-fill login form via injected JS
@router.api_route(
    "/audiobookshelf/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"],
)
async def proxy_abs(request: Request, path: str = ""):
    base = (settings.get("abs_url") or ABS_URL or "http://audiobookshelf:80").rstrip("/")
    resp = await _proxy(request, base + "/audiobookshelf", path)

    # Inject auto-login script into HTML responses
    ct = resp.headers.get("content-type", "")
    if "text/html" in ct and resp.status_code == 200:
        html = resp.body.decode("utf-8", errors="replace")
        if "audiobookshelf" in html.lower():
            script = _abs_autologin_script()
            html = html.replace("</head>", f"{script}</head>", 1)
            hdrs = {k: v for k, v in resp.headers.items()
                    if k.lower() not in ("content-length", "etag",
                                         "last-modified")}
            hdrs["cache-control"] = "no-cache, no-store, must-revalidate"
            return Response(
                content=html.encode("utf-8"),
                status_code=resp.status_code,
                headers=hdrs,
            )
    return resp


def _calibre_autologin_script() -> str:
    """JS that auto-fills and submits the Calibre-Web login form."""
    user = settings.get("calibre_user") or CALIBRE_USER or "admin"
    pwd = settings.get("calibre_pass") or CALIBRE_PASS or ""
    user_js = user.replace("\\", "\\\\").replace('"', '\\"')
    pwd_js = pwd.replace("\\", "\\\\").replace('"', '\\"')
    return f'''<script>
(function() {{
  if (sessionStorage.getItem("_calibre_autologin")) return;
  var uInput = document.querySelector('#username');
  var pInput = document.querySelector('#password');
  var btn = document.querySelector('button[name="submit"], button[type="submit"]');
  if (uInput && pInput && btn) {{
    sessionStorage.setItem("_calibre_autologin", "1");
    uInput.value = "{user_js}";
    pInput.value = "{pwd_js}";
    btn.click();
  }}
}})();
</script>'''


# Calibre-Web proxy with HTML rewriting and auto-login
@router.api_route(
    "/calibre/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"],
)
async def proxy_calibre(request: Request, path: str = ""):
    base = (settings.get("calibre_url") or "http://calibre-web:8083").rstrip("/")
    resp = await _proxy(request, base, path, rewrite_html=True, prefix="calibre")

    # Inject auto-login script if login page is detected
    ct = resp.headers.get("content-type", "")
    if "text/html" in ct and resp.status_code == 200:
        html = resp.body.decode("utf-8", errors="replace")
        if 'id="password"' in html and 'id="username"' in html:
            script = _calibre_autologin_script()
            html = html.replace("</body>", f"{script}</body>", 1)
            hdrs = {k: v for k, v in resp.headers.items()
                    if k.lower() not in ("content-length", "etag",
                                         "last-modified")}
            hdrs["cache-control"] = "no-cache, no-store, must-revalidate"
            return Response(
                content=html.encode("utf-8"),
                status_code=resp.status_code,
                headers=hdrs,
            )
    return resp
