"""OAuth2 PKCE authentication routes for TranscriberApp v2."""

import os
import secrets
import base64
import hashlib
import json
import time
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse, RedirectResponse

from backend.src.infrastructure.logging.logging_config import setup_logging

logger = setup_logging("transcribeapp")

router = APIRouter(tags=["auth"])

# In-memory store for PKCE state (one per browser tab, TTL 5 min)
_OAUTH_SESSIONS: dict = {}
_SESSION_EXPIRY_SECONDS = 300


def _cleanup_expired_sessions():
    now = time.time()
    expired = [k for k, v in _OAUTH_SESSIONS.items() if now - v["created_at"] > _SESSION_EXPIRY_SECONDS]
    for k in expired:
        del _OAUTH_SESSIONS[k]


def _get_config() -> dict:
    return {
        "oauth2_url": os.environ.get("PUBLIC_OAUTH2_URL", "http://localhost:8080").rstrip("/"),
        "oauth2_internal_url": os.environ.get("OAUTH2_URL", "http://localhost:8080").rstrip("/"),
        "client_id": os.environ.get("OAUTH2_CLIENT_ID", "transcriberapp"),
        "client_secret": os.environ.get("OAUTH2_CLIENT_SECRET", ""),
        "redirect_uri": os.environ.get("PUBLIC_REDIRECT_URI", "http://localhost:8002/oauth/callback"),
        "token_endpoint": os.environ.get("OAUTH2_TOKEN_ENDPOINT", "/oauth2/token"),
        "userinfo_endpoint": os.environ.get("OAUTH2_USERINFO_ENDPOINT", "/userinfo"),
    }


def _generate_code_verifier() -> str:
    return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode().rstrip("=")


def _generate_code_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).decode().rstrip("=")


@router.post("/api/auth/oauth2/start")
async def start_oauth2_flow(request: Request):
    if request.cookies.get("logged_in"):
        return JSONResponse(status_code=400, content={"success": False, "error": "Ya hay una sesión activa"})

    try:
        code_verifier = _generate_code_verifier()
        code_challenge = _generate_code_challenge(code_verifier)
        state = secrets.token_urlsafe(16)
        config = _get_config()

        state_data = {"s": state, "v": code_verifier}
        encoded_state = base64.urlsafe_b64encode(json.dumps(state_data).encode()).decode().rstrip("=")

        params = {
            "response_type": "code",
            "client_id": config["client_id"],
            "redirect_uri": config["redirect_uri"],
            "scope": "openid profile read write",
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "state": encoded_state,
            "prompt": "login",
        }

        auth_url = f"{config['oauth2_url']}/oauth2/authorize?{urlencode(params)}"
        logger.info(f"[OAUTH_START] URL generada: {auth_url[:100]}...")

        _OAUTH_SESSIONS[encoded_state] = {"code_verifier": code_verifier, "created_at": time.time()}

        return JSONResponse(content={"success": True, "authorization_url": auth_url})

    except Exception as e:
        logger.error(f"[OAUTH_START] Error: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})


@router.get("/oauth/callback")
async def oauth_callback(request: Request):
    _cleanup_expired_sessions()

    code = request.query_params.get("code")
    error = request.query_params.get("error")
    state = request.query_params.get("state")

    if error:
        return RedirectResponse(url=f"/login?error={error}", status_code=302)
    if not code or not state:
        return RedirectResponse(url="/login?error=missing_params", status_code=302)

    session_data = _OAUTH_SESSIONS.get(state)
    if not session_data:
        logger.warning(f"[OAUTH_CALLBACK] State no encontrado: {state[:30] if state else 'None'}")
        return RedirectResponse(url="/login?error=session_expired", status_code=302)

    code_verifier = session_data["code_verifier"]
    del _OAUTH_SESSIONS[state]

    config = _get_config()
    token_url = f"{config['oauth2_internal_url']}{config['token_endpoint']}"
    basic_token = base64.b64encode(f"{config['client_id']}:{config['client_secret']}".encode()).decode()

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            token_resp = await client.post(
                token_url,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": config["redirect_uri"],
                    "code_verifier": code_verifier,
                },
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Authorization": f"Basic {basic_token}",
                },
            )

            logger.info(f"[OAUTH_CALLBACK] Token response: {token_resp.status_code}")

            if token_resp.status_code != 200:
                logger.error(f"[OAUTH_CALLBACK] Token error: {token_resp.text}")
                return RedirectResponse(url="/login?error=token_exchange_failed", status_code=302)

            token_data = token_resp.json()
            access_token = token_data.get("access_token")

            userinfo_resp = await client.get(
                f"{config['oauth2_internal_url']}{config['userinfo_endpoint']}",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            user_info = userinfo_resp.json() if userinfo_resp.status_code == 200 else {
                "sub": "1", "email": "user@example.com", "preferred_username": "user"
            }

        is_secure = config["oauth2_url"].startswith("https")
        cookie_kwargs = {"httponly": True, "secure": is_secure, "samesite": "lax", "max_age": 86400}

        response = RedirectResponse(url="/", status_code=302)
        response.set_cookie("logged_in", "true", **cookie_kwargs)
        response.set_cookie("user_id", str(user_info.get("sub", "1")), **cookie_kwargs)
        response.set_cookie("email", user_info.get("email", ""), **cookie_kwargs)
        response.set_cookie("username", user_info.get("preferred_username", user_info.get("name", "user")), **cookie_kwargs)

        logger.info(f"[OAUTH_CALLBACK] Login exitoso: {user_info.get('preferred_username', 'user')}")
        return response

    except Exception as e:
        logger.error(f"[OAUTH_CALLBACK] Error: {e}", exc_info=True)
        return RedirectResponse(url=f"/login?error=internal_error", status_code=302)


@router.get("/api/auth/check")
async def check_auth(request: Request):
    if request.cookies.get("logged_in"):
        return {
            "logged_in": True,
            "user_id": request.cookies.get("user_id"),
            "username": request.cookies.get("username"),
            "email": request.cookies.get("email"),
        }
    return {"logged_in": False}


@router.post("/api/auth/logout")
async def logout(request: Request):
    response = JSONResponse(content={"success": True})
    for cookie in ("logged_in", "user_id", "email", "username"):
        response.delete_cookie(cookie)
    return response
