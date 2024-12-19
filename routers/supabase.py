import os

import logfire
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from managers.supabase import SupabaseManager

supabase_manager_cache = {}

supabase_router = APIRouter()


def get_access_token(request: Request) -> str:
    """リクエストヘッダーからアクセストークンを取得"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header missing or invalid")
    return auth_header.split("Bearer ")[1]


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
async def refresh(request: Request) -> str:
    try:
        refresh_token = request.cookies.get("refresh_token")
        supabase = SupabaseManager()
        tokens = supabase.refresh_access_token(refresh_token)
        logfire.info(f"refresh token user: {tokens["user_id"]}")

        supabase_manager_cache[tokens["access_token"]] = supabase
        return JSONResponse(content={"access_token": tokens["access_token"]})
    except HTTPException as e:
        raise e


@supabase_router.get("/supabase/signout")
async def signout(request: Request) -> str:
    try:
        access_token = get_access_token(request)
        supabase = get_supabase(access_token)
        user_id = supabase.get_user_id()
        supabase.supabase.auth.sign_out()
        logfire.info(f"sign out user: {user_id}")

        supabase_manager_cache.pop(access_token)

        # リフレッシュトークンを削除
        response = JSONResponse(content={"message": "Sign out"})
        response.set_cookie(
            key="refresh_token",
            value="",
            httponly=True,
            secure=True,
            samesite="Lax",
            max_age=0,
        )

        return response
    except HTTPException as e:
        raise e
