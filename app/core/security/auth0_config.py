"""Auth0設定モジュール"""
import os


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
    
    # Web App用のClient ID（将来的な利用のために保持）
    WEB_CLIENT_ID: str = os.getenv("AUTH0_WEB_CLIENT_ID", "")
    
    # Web App用のClient Secret（将来的な利用のために保持）
    WEB_CLIENT_SECRET: str = os.getenv("AUTH0_WEB_CLIENT_SECRET", "")

    # Auth0 Management API用のMachine to Machineクライアント情報
    MANAGEMENT_CLIENT_ID: str = os.getenv("AUTH0_MANAGEMENT_CLIENT_ID", WEB_CLIENT_ID)
    MANAGEMENT_CLIENT_SECRET: str = os.getenv("AUTH0_MANAGEMENT_CLIENT_SECRET", WEB_CLIENT_SECRET)
    
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

    @classmethod
    def get_management_audience(cls) -> str:
        """Management APIのAudienceを取得"""
        default_audience = f"https://{cls.DOMAIN}/api/v2/" if cls.DOMAIN else ""
        return os.getenv("AUTH0_MANAGEMENT_AUDIENCE", default_audience)

    @classmethod
    def has_management_credentials(cls) -> bool:
        """Management API呼び出しに必要な資格情報が揃っているか"""
        return all(
            [
                cls.DOMAIN,
                cls.MANAGEMENT_CLIENT_ID,
                cls.MANAGEMENT_CLIENT_SECRET,
                cls.get_management_audience(),
            ]
        )
