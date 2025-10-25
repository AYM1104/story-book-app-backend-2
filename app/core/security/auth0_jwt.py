"""Auth0 JWT検証モジュール"""
import json
from typing import Optional
from urllib.request import urlopen

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt, JWTError

from app.core.security.auth0_config import Auth0Config


# HTTPベアラートークン認証スキーム
http_bearer = HTTPBearer(auto_error=True)


def verify_auth0_token(token: str) -> dict:
    """Auth0が発行したJWTトークンを検証する
    
    Args:
        token: JWT トークン文字列
        
    Returns:
        デコードされたペイロード
        
    Raises:
        HTTPException: トークンが無効な場合
    """
    # Auth0の設定を検証
    Auth0Config.validate()
    
    # JWKS（公開鍵セット）を取得
    jwks_url = Auth0Config.get_jwks_url()
    
    try:
        # JWKSエンドポイントから公開鍵を取得
        jwks = json.loads(urlopen(jwks_url).read())
        
        # トークンのヘッダーを取得（署名検証なし）
        unverified_header = jwt.get_unverified_header(token)
        
        # 適切な公開鍵を探す
        rsa_key = {}
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"]
                }
                break
        
        if not rsa_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="適切な公開鍵が見つかりません",
            )
        
        # トークンを検証してデコード
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=Auth0Config.ALGORITHMS,
            audience=Auth0Config.API_AUDIENCE,
            issuer=Auth0Config.get_issuer(),
        )
        
        return payload
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="トークンの有効期限が切れています",
        )
    except jwt.JWTClaimsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="トークンのクレームが無効です（audience/issuerを確認してください）",
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"トークンの検証に失敗しました: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"認証処理中にエラーが発生しました: {str(e)}",
        )


def get_current_user_auth0(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer)
) -> dict:
    """Auth0トークンを検証し、現在のユーザー情報を返す
    
    FastAPIの依存性注入で使用する関数
    
    Args:
        credentials: HTTPベアラートークン
        
    Returns:
        ユーザー情報を含むペイロード
        - sub: ユーザーID（Auth0のユーザーID）
        - email: メールアドレス（存在する場合）
        - その他のクレーム
    """
    token = credentials.credentials
    payload = verify_auth0_token(token)
    
    # ユーザーIDが存在するか確認
    if "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="トークンにユーザーIDが含まれていません",
        )
    
    return payload


def get_user_id_auth0(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer)
) -> str:
    """Auth0トークンからユーザーIDのみを取得する
    
    Args:
        credentials: HTTPベアラートークン
        
    Returns:
        ユーザーID（Auth0のsub）
    """
    payload = get_current_user_auth0(credentials)
    return payload["sub"]

