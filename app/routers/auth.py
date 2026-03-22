from fastapi import APIRouter, HTTPException, Depends, Request
from app.models import LoginRequest, CreateUserRequest, ChangePasswordRequest
from app.services import auth

router = APIRouter(prefix="/api/auth", tags=["auth"])

_login_attempts: dict[str, list[float]] = {}


@router.post("/login")
async def login(req: LoginRequest, request: Request):
    ip = request.client.host if request.client else "unknown"
    now = __import__("time").time()
    attempts = _login_attempts.get(ip, [])
    attempts = [t for t in attempts if now - t < 300]
    if len(attempts) >= 5:
        raise HTTPException(429, "Too many login attempts")
    token = auth.login(req.username, req.password)
    if not token:
        attempts.append(now)
        _login_attempts[ip] = attempts
        raise HTTPException(401, "Invalid credentials")
    _login_attempts.pop(ip, None)
    return {"token": token}


@router.get("/me")
async def me(user: dict = Depends(auth.get_current_user)):
    return user


@router.get("/users")
async def list_users(user: dict = Depends(auth.require_admin)):
    return auth.list_users()


@router.post("/users")
async def create_user(req: CreateUserRequest, user: dict = Depends(auth.require_admin)):
    try:
        ok = auth.create_user(req.username, req.password, req.is_admin)
    except ValueError as e:
        raise HTTPException(400, str(e))
    if not ok:
        raise HTTPException(409, "User already exists")
    return {"status": "created"}


@router.delete("/users/{username}")
async def delete_user(username: str, user: dict = Depends(auth.require_admin)):
    if username == user["username"]:
        raise HTTPException(400, "Cannot delete yourself")
    if not auth.delete_user(username):
        raise HTTPException(404, "User not found")
    return {"status": "deleted"}


@router.put("/users/{username}/password")
async def change_password(username: str, req: ChangePasswordRequest,
                          user: dict = Depends(auth.get_current_user)):
    if username != user["username"] and not user.get("is_admin"):
        raise HTTPException(403, "Not allowed")
    try:
        auth.change_password(username, req.new_password)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"status": "updated"}
