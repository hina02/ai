import logfire
from fastapi import APIRouter, Cookie, Depends, Header, HTTPException
from fastapi.responses import JSONResponse

from config import settings
from managers.supabase import SupabaseManager

supabase = None
supabase_manager_cache = {}

supabase_router = APIRouter()


def get_access_token(authorization: str = Header(...)) -> str:
    """リクエストヘッダーからアクセストークンを取得"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header missing or invalid")
    return authorization.split("Bearer ")[1]


def get_supabase_dev() -> SupabaseManager:
    email = settings.supabase_dev_email
    password = settings.supabase_dev_password
    global supabase
    if supabase is None:
        supabase = SupabaseManager()
        supabase.sign_in_with_password(email, password)
    return supabase


def get_supabase(access_token: str = Depends(get_access_token)) -> SupabaseManager:
    if access_token in supabase_manager_cache:
        return supabase_manager_cache[access_token]
    else:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def get_supabase_wb(access_token: str) -> SupabaseManager:
    if access_token in supabase_manager_cache:
        return supabase_manager_cache[access_token]
    else:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


@supabase_router.get("/supabase/signin")
async def signin(email: str, password: str) -> str:
    try:
        supabase = SupabaseManager()
        tokens = supabase.sign_in_with_password(email, password)
        logfire.info(f"sign in user: {tokens["user_id"]}")

        supabase_manager_cache[tokens["access_token"]] = supabase
        response = JSONResponse(content={"access_token": tokens["access_token"]})

        # リフレッシュトークンを HttpOnly Cookie に保存
        response.set_cookie(
            key="refresh_token",
            value=tokens["refresh_token"],
            httponly=True,
            secure=True,
            samesite="Lax",
        )
        return response
    except HTTPException as e:
        raise e


@supabase_router.get("/supabase/refresh")
async def refresh(refresh_token: str = Cookie(...)) -> str:
    try:
        supabase = SupabaseManager()
        tokens = supabase.refresh_access_token(refresh_token)
        logfire.info(f"refresh token user: {tokens["user_id"]}")

        supabase_manager_cache[tokens["access_token"]] = supabase
        return JSONResponse(content={"access_token": tokens["access_token"]})
    except HTTPException as e:
        raise e


@supabase_router.get("/supabase/signout")
async def signout(access_token=Depends(get_access_token)) -> str:
    try:
        supabase = get_supabase(access_token)
        user_id = supabase.get_user_id()
        supabase.supabase.auth.sign_out()
        logfire.info(f"sign out user: {user_id}")

        supabase_manager_cache.pop(access_token)

        # リフレッシュトークンを削除
        response = JSONResponse(content={"message": "Sign out"})
        response.delete_cookie(
            key="refresh_token",
            httponly=True,
            secure=True,
            samesite="Lax",
        )
        return response
    except HTTPException as e:
        raise e
