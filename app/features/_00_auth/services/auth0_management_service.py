"""Auth0 Management APIを利用したユーザー操作ユーティリティ"""
from __future__ import annotations

import time
from typing import Optional

import requests

from app.core.security.auth0_config import Auth0Config


class Auth0ManagementService:
    """Auth0の管理APIを介してユーザーを操作するサービス"""

    def __init__(self) -> None:
        self._access_token: Optional[str] = None
        self._token_expiry: float = 0.0

    @staticmethod
    def _has_management_credentials() -> bool:
        # Management API用の資格情報を確実に初期化
        Auth0Config._init_management_credentials()
        return Auth0Config.has_management_credentials()

    def _get_management_token(self) -> str:
        # Management API用の資格情報を確実に初期化
        Auth0Config._init_management_credentials()
        
        if not self._has_management_credentials():
            raise ValueError(
                "Auth0 management credentials are not configured. "
                "Set AUTH0_MANAGEMENT_CLIENT_ID and AUTH0_MANAGEMENT_CLIENT_SECRET."
            )

        now = time.time()
        if self._access_token and now < (self._token_expiry - 60):
            return self._access_token

        token_url = f"https://{Auth0Config.DOMAIN}/oauth/token"
        payload = {
            "grant_type": "client_credentials",
            "client_id": Auth0Config.MANAGEMENT_CLIENT_ID,
            "client_secret": Auth0Config.MANAGEMENT_CLIENT_SECRET,
            "audience": Auth0Config.get_management_audience(),
        }

        response = requests.post(token_url, json=payload, timeout=15)
        response.raise_for_status()
        data = response.json()

        access_token = data.get("access_token")
        expires_in = data.get("expires_in", 3600)

        if not access_token:
            raise ValueError("Auth0 management token response did not contain access_token")

        self._access_token = access_token
        self._token_expiry = now + expires_in
        return access_token

    def delete_user(self, user_id: str) -> bool:
        """Auth0上のユーザーを削除する"""

        if not self._has_management_credentials():
            raise ValueError(
                "Auth0 management credentials are not configured. "
                "Set AUTH0_MANAGEMENT_CLIENT_ID and AUTH0_MANAGEMENT_CLIENT_SECRET."
            )

        token = self._get_management_token()
        url = f"https://{Auth0Config.DOMAIN}/api/v2/users/{user_id}"
        headers = {"Authorization": f"Bearer {token}"}

        response = requests.delete(url, headers=headers, timeout=15)

        if response.status_code in (200, 202, 204):
            return True
        if response.status_code == 404:
            # 既に削除済みであれば成功扱い
            return True

        detail = response.text or "Unknown error"
        raise RuntimeError(f"Failed to delete Auth0 user: {response.status_code} {detail}")


auth0_management_service = Auth0ManagementService()

