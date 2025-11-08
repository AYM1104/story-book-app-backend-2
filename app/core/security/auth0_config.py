"""Auth0設定モジュール"""
import os
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()


def _clean_env_var(value: str) -> str:
    """環境変数から改行文字や空白を削除"""
    if not value:
        return ""
    return value.strip().replace("\n", "").replace("\r", "")


class Auth0Config:
    """Auth0の設定情報を管理するクラス"""
    
    # Auth0ドメイン（例: your-domain.auth0.com）
    DOMAIN: str = _clean_env_var(os.getenv("AUTH0_DOMAIN", ""))
    
    # Auth0 API Audience（バックエンドAPI用）
    API_AUDIENCE: str = _clean_env_var(os.getenv("AUTH0_API_AUDIENCE", ""))
    
    # Auth0アルゴリズム（通常はRS256）
    ALGORITHMS: list[str] = ["RS256"]
    
    # Native App用のClient ID（SwiftUIアプリ用）
    NATIVE_CLIENT_ID: str = _clean_env_var(os.getenv("AUTH0_NATIVE_CLIENT_ID", ""))
    
    # Web App用のClient ID（将来的な利用のために保持）
    WEB_CLIENT_ID: str = _clean_env_var(os.getenv("AUTH0_WEB_CLIENT_ID", ""))
    
    # Web App用のClient Secret（将来的な利用のために保持）
    WEB_CLIENT_SECRET: str = _clean_env_var(os.getenv("AUTH0_WEB_CLIENT_SECRET", ""))
    
    # Auth0 Management API用のMachine to Machineクライアント情報
    # 環境変数が設定されていない場合は、WEB_CLIENT_IDとWEB_CLIENT_SECRETを使用
    _temp_management_client_id: str = _clean_env_var(os.getenv("AUTH0_MANAGEMENT_CLIENT_ID", ""))
    _temp_management_client_secret: str = _clean_env_var(os.getenv("AUTH0_MANAGEMENT_CLIENT_SECRET", ""))
    
    @classmethod
    def _init_management_credentials(cls):
        """Management API用の資格情報を初期化（クラス変数の初期化後に呼び出す）"""
        if not hasattr(cls, '_management_initialized'):
            cls.MANAGEMENT_CLIENT_ID = cls._temp_management_client_id if cls._temp_management_client_id else cls.WEB_CLIENT_ID
            cls.MANAGEMENT_CLIENT_SECRET = cls._temp_management_client_secret if cls._temp_management_client_secret else cls.WEB_CLIENT_SECRET
            cls._management_initialized = True
    
    # クラス変数の初期化後に設定される
    MANAGEMENT_CLIENT_ID: str = ""
    MANAGEMENT_CLIENT_SECRET: str = ""
    
    @classmethod
    def validate(cls) -> bool:
        """必須の設定が存在するかチェック"""
        # Management API用の資格情報を初期化
        cls._init_management_credentials()
        
        missing_vars = []
        if not cls.DOMAIN:
            missing_vars.append("AUTH0_DOMAIN")
        if not cls.API_AUDIENCE:
            missing_vars.append("AUTH0_API_AUDIENCE")
        
        if missing_vars:
            error_msg = (
                f"以下のAuth0環境変数が設定されていません: {', '.join(missing_vars)}\n"
                f"設定方法:\n"
                f"  ローカル環境: .envファイルに設定するか、環境変数をエクスポートしてください\n"
                f"  Cloud Run: gcloud run services update コマンドで環境変数を設定してください\n"
                f"  例: export AUTH0_DOMAIN=your-domain.auth0.com"
            )
            raise ValueError(error_msg)
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
        # Management API用の資格情報を初期化
        cls._init_management_credentials()
        
        return all(
            [
                cls.DOMAIN,
                cls.MANAGEMENT_CLIENT_ID,
                cls.MANAGEMENT_CLIENT_SECRET,
                cls.get_management_audience(),
            ]
        )
