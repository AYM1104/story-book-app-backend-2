"""Auth0 JWT検証モジュール"""
import json
from typing import Optional
from urllib.request import urlopen

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.core.security.auth0_config import Auth0Config


# HTTPベアラートークン認証スキーム
# auto_error=Falseにして、トークンが存在しない場合でもエンドポイントに到達できるようにする
http_bearer = HTTPBearer(auto_error=False)


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
        
        # デバッグ用: トークンのペイロードを検証なしでデコードして確認
        unverified_payload = None
        try:
            unverified_payload = jwt.decode(token, options={"verify_signature": False})
            token_aud = unverified_payload.get('aud')
            token_iss = unverified_payload.get('iss')
            expected_aud = Auth0Config.API_AUDIENCE
            expected_iss = Auth0Config.get_issuer()
            
            print(f"🔍 トークン内のaudience: {token_aud} (型: {type(token_aud)})")
            print(f"🔍 トークン内のissuer: {token_iss}")
            print(f"🔍 期待されるaudience: {expected_aud}")
            print(f"🔍 期待されるissuer: {expected_iss}")
            
            # audienceがリスト形式の場合の処理
            if isinstance(token_aud, list):
                print(f"🔍 audienceはリスト形式です: {token_aud}")
                if expected_aud not in token_aud:
                    print(f"⚠️ 期待されるaudience '{expected_aud}' がリストに含まれていません")
        except Exception as e:
            print(f"⚠️ トークンのデバッグ情報取得エラー: {e}")
        
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
    except jwt.JWTClaimsError as e:
        # トークンの詳細情報を取得してエラーメッセージに含める
        error_message = str(e)
        try:
            unverified_payload = jwt.decode(token, options={"verify_signature": False})
            token_aud = unverified_payload.get('aud')
            token_iss = unverified_payload.get('iss')
            
            # audienceがリスト形式の場合の処理
            aud_display = token_aud
            if isinstance(token_aud, list):
                aud_display = f"{token_aud} (リスト形式)"
            
            error_message = (
                f"トークンのクレームが無効です（audience/issuerを確認してください）\n"
                f"エラー詳細: {error_message}\n"
                f"トークン内のaudience: {aud_display}\n"
                f"トークン内のissuer: {token_iss}\n"
                f"期待されるaudience: {Auth0Config.API_AUDIENCE}\n"
                f"期待されるissuer: {Auth0Config.get_issuer()}"
            )
        except Exception as parse_error:
            error_message = f"トークンのクレームが無効です（audience/issuerを確認してください）\nエラー詳細: {error_message}\n(デバッグ情報取得エラー: {parse_error})"
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_message,
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
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer)
) -> dict:
    """Auth0トークンを検証し、現在のユーザー情報を返す
    
    FastAPIの依存性注入で使用する関数。
    JWTトークンの全ペイロードを返します。
    
    Args:
        credentials: HTTPベアラートークン（auto_error=FalseのためOptional）
        
    Returns:
        ユーザー情報を含むペイロード辞書
        - sub: Auth0のユーザー識別子（users.idとして使用）
        - email: メールアドレス（存在する場合）
        - name: ユーザー名（存在する場合）
        - その他のクレーム
        
    Raises:
        HTTPException: トークンが存在しない場合、または無効な場合
    """
    # トークンが存在しない場合のエラーハンドリング
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="認証トークンが必要です。AuthorizationヘッダーにBearerトークンを設定してください。",
        )
    
    token = credentials.credentials
    payload = verify_auth0_token(token)
    
    # subクレームが存在するか確認
    if "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="トークンにユーザーID（sub）が含まれていません",
        )
    
    return payload


def get_auth0_sub_from_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer)
) -> str:
    """Auth0 JWTトークンから`sub`クレームを取得する
    
    JWTトークンの`sub`クレームはAuth0のユーザー識別子で、
    データベースの`users.id`として使用されます。
    
    Args:
        credentials: HTTPベアラートークン（auto_error=FalseのためOptional）
        
    Returns:
        Auth0の`sub`クレーム（例: "auth0|123456789"）
        この値はデータベースのuser_idとして使用される
        
    Raises:
        HTTPException: トークンが存在しない場合、または無効な場合
    """
    payload = get_current_user_auth0(credentials)
    return payload["sub"]

# 後方互換性のためのエイリアス（将来的に削除予定）
get_user_id_auth0 = get_auth0_sub_from_token


def get_user_or_create(
    payload: dict = Depends(get_current_user_auth0),
    db: Session = None  # 使用時にget_supabase_dbを注入
):
    """JWTトークンからユーザーを取得、存在しない場合は自動作成する
    
    初回ログイン時にJWTから`sub`を取得し、DBにユーザーが存在しない場合は
    自動作成して300クレジットを付与します（仕様書の要件に準拠）。
    
    この関数は依存性注入用ではありません。実際の使用時は以下のようにしてください：
    
    ```python
    from app.database.supabase_session import get_supabase_db
    from app.models.users.users import Users
    from app.service.credits import CreditsService
    from app.models.credits.subscription import PlanType
    
    @router.get("/some-endpoint")
    def some_endpoint(
        payload: dict = Depends(get_current_user_auth0),
        db: Session = Depends(get_supabase_db)
    ):
        user = get_user_or_create(payload, db)
        # ...
    ```
    
    Args:
        payload: JWTペイロード（get_current_user_auth0から取得）
        db: データベースセッション（必須）
        
    Returns:
        Usersオブジェクト（作成または取得されたユーザー）
    """
    if db is None:
        raise ValueError("データベースセッション（db）が必要です")
    
    # JWTのsubクレームを取得（Auth0ユーザーID = DBのusers.id）
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="トークンにユーザーID（sub）が含まれていません",
        )
    
    # ユーザーを検索
    from app.models.users.users import Users
    from app.service.credits import CreditsService
    from app.models.credits.subscription import PlanType
    
    user = db.query(Users).filter(Users.id == sub).first()
    
    if not user:
        # ユーザーが存在しない場合：初回ログイン時の自動作成
        try:
            # デバッグ: トークンのペイロード内容をログ出力
            print(f"🔍 ユーザー作成: sub={sub}")
            print(f"🔍 トークンペイロード: email={payload.get('email')}, name={payload.get('name')}, picture={payload.get('picture')}")
            print(f"🔍 全ペイロードキー: {list(payload.keys())}")
            
            # ユーザー名を取得（Google認証などでnameが含まれている場合）
            user_name = payload.get("name") or ""
            
            # nameが取得できない場合、emailから名前部分を抽出
            if not user_name:
                email = payload.get("email") or ""
                if email:
                    # emailの@マークより前の部分をユーザー名として使用
                    user_name = email.split("@")[0]
            
            # それでも取得できない場合、デフォルト値を使用
            if not user_name:
                user_name = f"ユーザー_{sub[-8:]}"  # subの最後8文字を使用して一意性を確保
            
            # emailを取得（実機ではemailが含まれていない可能性がある）
            email = payload.get("email") or ""
            
            # emailが空の場合、subベースのダミーemailを生成（unique制約を満たすため）
            if not email:
                # subからダミーemailを生成（例: auth0|123456789 -> auth0-123456789@dummy.local）
                email = f"{sub.replace('|', '-')}@dummy.local"
                print(f"⚠️ emailが含まれていないため、ダミーemailを生成: {email}")
            
            user = Users(
                id=sub,  # Auth0のsubクレーム
                user_name=user_name,  # Google認証などから取得した名前
                email=email  # Auth0から取得可能なメールアドレス（存在しない場合はダミー）
            )
            db.add(user)
            db.flush()  # IDを取得するためにflush
            
            # 初回登録時の300クレジット付与
            try:
                CreditsService.add_credits(
                    db=db,
                    user_id=sub,
                    amount=300,
                    reason="signup_bonus"
                )
            except Exception as credits_error:  # noqa: BLE001
                db.rollback()
                import traceback
                error_traceback = traceback.format_exc()
                print(f"❌ クレジット付与エラー: {str(credits_error)}")
                print(f"❌ トレースバック:\n{error_traceback}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"クレジット付与に失敗しました: {str(credits_error)}",
                )
            
            # FREEプランのサブスクリプションを作成
            try:
                CreditsService.ensure_subscription(
                    db=db,
                    user_id=sub,
                    plan=PlanType.FREE
                )
            except Exception as subscription_error:  # noqa: BLE001
                db.rollback()
                import traceback
                error_traceback = traceback.format_exc()
                print(f"❌ サブスクリプション作成エラー: {str(subscription_error)}")
                print(f"❌ トレースバック:\n{error_traceback}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"サブスクリプション作成に失敗しました: {str(subscription_error)}",
                )
            
            # 最後にコミット（CreditsService内で既にコミットされているが、念のため）
            try:
                db.commit()
                db.refresh(user)
            except Exception as commit_error:  # noqa: BLE001
                db.rollback()
                import traceback
                error_traceback = traceback.format_exc()
                print(f"❌ コミットエラー: {str(commit_error)}")
                print(f"❌ トレースバック:\n{error_traceback}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"データベースコミットに失敗しました: {str(commit_error)}",
                )
        except HTTPException:
            # HTTPExceptionはそのまま再スロー
            raise
        except Exception as e:  # noqa: BLE001
            # その他のエラーはロールバックしてから再スロー
            db.rollback()
            import traceback
            error_traceback = traceback.format_exc()
            print(f"❌ ユーザー作成エラー: {str(e)}")
            print(f"❌ トレースバック:\n{error_traceback}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"ユーザー作成に失敗しました: {str(e)}",
            )
    
    return user

