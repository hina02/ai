import os

from fastapi import HTTPException, Request
from supabase import Client, create_client

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_ANON_KEY")


class SupabaseManager:
    def __init__(self, access_token: str | None = None):
        self.supabase: Client = create_client(url, key)
        if access_token:
            self.assert_session(access_token=access_token)

    def sign_in_with_password(self, email: str, password: str) -> dict:
        try:
            response = self.supabase.auth.sign_in_with_password(
                {"email": email, "password": password}
            )
            return {
                "user_id": response.user.id,
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
            }
        except Exception as e:
            raise HTTPException(status_code=401, detail=str(e))

    def refresh_access_token(self, refresh_token: str) -> dict:
        try:
            response = self.supabase.auth.refresh_session(refresh_token)
            return {
                "user_id": response.user.id,
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
            }
        except Exception as e:
            raise HTTPException(status_code=401, detail=str(e))

    def assert_session(self, access_token: str) -> bool:
        response = self.supabase.auth.get_user(access_token)
        print(response.user.id)
        if not response:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        return True

    def get_user_id(self) -> str | None:
        user = self.supabase.auth.get_user()
        return user.user.id if user else None
