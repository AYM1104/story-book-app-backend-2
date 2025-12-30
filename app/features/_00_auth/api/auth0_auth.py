"""Auth0認証APIエンドポイント"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security.auth0_jwt import get_current_user_auth0, get_auth0_sub_from_token, get_user_or_create
from app.database.supabase_session import get_supabase_db
from app.features._00_auth.schemas.auth0 import (
    AccountDeletionResponse,
    Auth0CleanupResponse,
    StorageCleanupResponse,
    UserInfoResponse,
)
from app.service.user_account_cleanup_service import user_account_cleanup_service


router = APIRouter(prefix="/auth0", tags=["auth0"])

# Auth0でユーザー情報を取得するためのエンドポイント
@router.get("/me", response_model=UserInfoResponse)
def get_me_auth0(
    payload: dict = Depends(get_current_user_auth0),
    db: Session = Depends(get_supabase_db)
):
    """Auth0トークンを検証し、ユーザー情報を返す
    
    このエンドポイントは、SwiftUIアプリからAuth0でログイン後に
    ユーザー情報を取得するために使用します。
    
    初回ログインの場合は自動的にユーザーを作成し、300クレジットを付与します。
    
    Args:
        payload: Auth0トークンのペイロード（自動的に検証される）
        db: データベースセッション
        
    Returns:
        ユーザー情報
    """
    try:
        # デバッグ: リクエスト情報をログ出力
        print(f"🔍 /auth0/me エンドポイントに到達しました")
        print(f"🔍 payload keys: {list(payload.keys()) if payload else 'None'}")
        print(f"🔍 payload sub: {payload.get('sub') if payload else 'None'}")
        
        # ユーザーを取得または作成（初回ログイン時は自動作成＋300クレジット付与）
        user = get_user_or_create(payload, db)
        
        # メールアドレスが空文字列の場合、Noneに変換
        email = user.email if user.email and user.email != "" else None
        
        # user_nameがNULLまたは空文字列の場合、デフォルト値を設定
        user_name = user.user_name
        if not user_name or user_name == "":
            # メールアドレスからユーザー名を生成、またはデフォルト値を設定
            if email:
                user_name = email.split("@")[0]
            else:
                user_name = f"ユーザー_{user.id[-8:]}"  # IDの最後8文字を使用
        
        # JWTのsubクレームをuser_idとして返す（sub = Auth0ユーザーID = DBのusers.id）
        return UserInfoResponse(
            user_id=payload.get("sub", ""),  # Auth0のsubクレーム
            user_name=user_name,  # データベースから取得したユーザー名（NULLの場合はデフォルト値）
            email=email,  # データベースから取得したメールアドレス（空の場合はNone）
            name=payload.get("name"),  # Auth0から取得した名前（後方互換性のため）
            picture=payload.get("picture"),  # Auth0から取得した画像URL
        )
    except HTTPException as http_exc:
        # HTTPExceptionはそのまま再スロー（詳細なエラーメッセージを保持）
        print(f"❌ /auth0/me HTTPException: {http_exc.status_code} - {http_exc.detail}")
        raise
    except Exception as exc:  # noqa: BLE001
        # その他のエラーは詳細なエラーメッセージと共に500エラーを返す
        import traceback
        error_traceback = traceback.format_exc()
        print(f"❌ /auth0/me エラー: {str(exc)}")
        print(f"❌ トレースバック:\n{error_traceback}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ユーザー情報取得エラー: {str(exc)}",
        )

# Auth0トークンの有効性を確認するためのエンドポイント
@router.get("/verify")
def verify_token(user_id: str = Depends(get_auth0_sub_from_token)):
    """トークンの有効性を確認する
    
    シンプルなトークン検証エンドポイント。
    Auth0のsubクレーム（ユーザー識別子）を返します。
    
    Args:
        user_id: Auth0のsubクレーム（JWTから自動的に検証・取得される）
        
    Returns:
        検証結果とユーザーID
    """

    # 正常な場合はTrueとユーザーIDを返す
    return {
        "valid": True,
        "user_id": user_id,  # Auth0のsubクレーム
    }

# ユーザーアカウントと関連データを削除するためのエンドポイント
@router.delete("/me", response_model=AccountDeletionResponse)
def delete_my_account(
    payload: dict = Depends(get_current_user_auth0),
    db: Session = Depends(get_supabase_db),
):
    """現在のユーザーアカウントと関連データを削除するエンドポイント

    Auth0 にログイン済みのユーザーが「アカウント削除」を実行した際に呼び出され、
    ユーザー情報および関連テーブルのデータ、GCS 上に保存されたアップロード画像と
    生成済みの画像データ、Auth0 上のユーザー情報をまとめて削除する。

    Args:
        payload: 認証済みユーザーの JWT ペイロード（`sub` から Auth0 ユーザーIDを取得）
        db: Supabase 接続用の DB セッション

    Returns:
        AccountDeletionResponse: 削除結果の詳細（削除件数やストレージ・Auth0 クリーンアップ状況）
    """

    # JWTのsubクレームを取得（Auth0ユーザーID = DBのusers.id）
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ユーザーID（sub）を取得できませんでした",
        )

    # ユーザーアカウントと関連データを削除
    print(f"🗑️ [アカウント削除] ユーザーID: {user_id} のアカウント削除を開始します")
    try:
        # ユーザーアカウントと関連データを削除
        result = user_account_cleanup_service.delete_user_account(user_id=user_id, db=db)
        
        # 削除結果をログ出力
        print(f"📊 [アカウント削除] 削除結果:")
        print(f"  - 絵本: {result['deleted_storybooks']}件")
        print(f"  - プロット: {result['deleted_story_plots']}件")
        print(f"  - 設定: {result['deleted_story_settings']}件")
        print(f"  - 画像: {result['deleted_upload_images']}件")
        print(f"  - ストレージクリーンアップ: enabled={result['storage_cleanup']['enabled']}, error={result['storage_cleanup'].get('error')}")
        print(f"  - Auth0クリーンアップ: enabled={result['auth0_cleanup']['enabled']}, removed={result['auth0_cleanup']['account_removed']}, error={result['auth0_cleanup'].get('error')}")

    except ValueError:
        # ユーザーが見つからない場合は404エラーを返す
        print(f"❌ [アカウント削除] ユーザーが見つかりません: {user_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    except Exception as exc:  # noqa: BLE001
        # その他のエラーは500エラーを返す
        print(f"❌ [アカウント削除] エラーが発生しました: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"アカウント削除に失敗しました: {exc}",
        )

    # 削除結果を返す
    print(f"✅ [アカウント削除] ユーザーID: {user_id} のアカウント削除が完了しました")
    return AccountDeletionResponse(
        message="アカウントを削除しました",
        user_id=result["user_id"],
        deleted_storybooks=result["deleted_storybooks"],    # 削除した絵本の数
        deleted_story_plots=result["deleted_story_plots"],    # 削除した物語の数
        deleted_story_settings=result["deleted_story_settings"],    # 削除した物語の設定の数
        deleted_upload_images=result["deleted_upload_images"],    # 削除したアップロード画像の数
        storage_cleanup=StorageCleanupResponse(**result["storage_cleanup"]),    # ストレージのクリーンアップ状況
        auth0_cleanup=Auth0CleanupResponse(**result["auth0_cleanup"]),    # Auth0のクリーンアップ状況
    )   

# Auth0認証システムのヘルスチェックエンドポイント
@router.get("/health")
def health_check():
    """Auth0認証システムのヘルスチェック
    
    認証なしでアクセス可能なエンドポイント。
    Auth0の設定が正しいか確認します。
    """
    # Auth0Configクラスをインポート
    from app.core.security.auth0_config import Auth0Config
    
    # Auth0Configクラスを検証
    try:
        Auth0Config.validate()
        # 正常な場合はステータス、ドメイン、発行者を返す
        return {
            "status": "ok",
            "auth0_domain": Auth0Config.DOMAIN,
            "issuer": Auth0Config.get_issuer(),
        }
    except ValueError as e:
        # エラーが発生した場合は500エラーを返す
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Auth0設定エラー: {str(e)}",
        )

