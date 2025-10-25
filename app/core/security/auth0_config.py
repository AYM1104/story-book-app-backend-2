"""Auth0設定モジュール"""
import os
from typing import Optional


class Auth0Config:
    """Auth0の設定情報を管理するクラス"""
    
    # Auth0ドメイン（例: your-domain.auth0.com）
    DOMAIN: str = os.getenv("AUTH0_DOMAIN", "")
    
    # Auth0 API Audience（バックエンドAPI用）
    API_AUDIENCE: str = os.getenv("AUTH0_API_AUDIENCE", "")
    
    # Auth0アルゴリズム（通常はRS256）
    ALGORITHMS: list[str] = ["RS256"]
    
    # Native App用のClient ID（SwiftUIアプリ用）
    NATIVE_CLIENT_ID: str = os.getenv("AUTH0_NATIVE_CLIENT_ID", "")
    
    # Web App用のClient ID（バックエンド用）
    WEB_CLIENT_ID: str = os.getenv("AUTH0_WEB_CLIENT_ID", "")
    
    # Web App用のClient Secret（バックエンド用）
    WEB_CLIENT_SECRET: str = os.getenv("AUTH0_WEB_CLIENT_SECRET", "")
    
    @classmethod
    def validate(cls) -> bool:
        """必須の設定が存在するかチェック"""
        if not cls.DOMAIN:
            raise ValueError("AUTH0_DOMAINが設定されていません")
        if not cls.API_AUDIENCE:
            raise ValueError("AUTH0_API_AUDIENCEが設定されていません")
        return True
    
    @classmethod
    def get_issuer(cls) -> str:
        """IssuerのURL（https://your-domain.auth0.com/）を取得"""
        return f"https://{cls.DOMAIN}/"
    
    @classmethod
    def get_jwks_url(cls) -> str:
        """JWKS（JSON Web Key Set）のURLを取得"""
        return f"https://{cls.DOMAIN}/.well-known/jwks.json"

