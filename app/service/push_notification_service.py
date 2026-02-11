"""
プッシュ通知サービス

APNs（Apple Push Notification service）を使用してプッシュ通知を送信する。
"""

import os
import json
import time
import jwt
import httpx
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from app.models.device_token import DeviceToken


class PushNotificationService:
    """APNsプッシュ通知送信サービス"""
    
    def __init__(self):
        # APNs設定
        self.team_id = os.getenv("APNS_TEAM_ID")
        self.key_id = os.getenv("APNS_KEY_ID")
        self.bundle_id = os.getenv("APNS_BUNDLE_ID", "com.ehonnotane.app")
        
        # 環境に応じてエンドポイントを切り替え
        use_sandbox = os.getenv("APNS_USE_SANDBOX", "true").lower() == "true"
        if use_sandbox:
            self.apns_host = "https://api.sandbox.push.apple.com"
        else:
            self.apns_host = "https://api.push.apple.com"
        
        # APNs認証キーの読み込み（環境変数 or ファイル）
        self.auth_key = os.getenv("APNS_AUTH_KEY")
        if self.auth_key:
            # 環境変数から読み込んだ場合、改行を復元
            self.auth_key = self.auth_key.replace("\\n", "\n")
        else:
            # .p8ファイルから読み込み
            key_path = os.getenv("APNS_AUTH_KEY_PATH", "certs/apns_auth_key.p8")
            try:
                from pathlib import Path
                # backendディレクトリ基準で解決（service/ -> app/ -> backend/）
                base_dir = Path(__file__).resolve().parent.parent.parent
                full_path = base_dir / key_path
                if full_path.exists():
                    self.auth_key = full_path.read_text()
                    print(f"✅ APNs認証キーをファイルから読み込みました: {full_path}")
                else:
                    print(f"⚠️ APNs認証キーファイルが見つかりません: {full_path}")
            except Exception as e:
                print(f"⚠️ APNs認証キーの読み込みに失敗: {e}")
        
        self._token: Optional[str] = None
        self._token_expiry: float = 0
    
    def _is_configured(self) -> bool:
        """APNsが設定されているか確認"""
        return all([self.team_id, self.key_id, self.auth_key])
    
    def _generate_jwt_token(self) -> str:
        """APNs認証用のJWTトークンを生成"""
        current_time = time.time()
        
        # トークンが有効期限内ならキャッシュを使用（50分で更新）
        if self._token and current_time < self._token_expiry:
            return self._token
        
        # JWTペイロード
        payload = {
            "iss": self.team_id,
            "iat": int(current_time)
        }
        
        # JWTヘッダー
        headers = {
            "alg": "ES256",
            "kid": self.key_id
        }
        
        # トークン生成
        self._token = jwt.encode(
            payload,
            self.auth_key,
            algorithm="ES256",
            headers=headers
        )
        self._token_expiry = current_time + 3000  # 50分有効
        
        return self._token
    
    async def send_notification(
        self,
        device_token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        badge: Optional[int] = None,
        sound: str = "default"
    ) -> Dict[str, Any]:
        """
        単一デバイスにプッシュ通知を送信
        
        Args:
            device_token: APNsデバイストークン
            title: 通知タイトル
            body: 通知本文
            data: カスタムデータ（オプション）
            badge: バッジ数（オプション）
            sound: 通知音（デフォルト: "default"）
        
        Returns:
            送信結果
        """
        if not self._is_configured():
            print("⚠️ APNsが設定されていません。通知をスキップします。")
            return {"success": False, "error": "APNs not configured"}
        
        try:
            # JWT認証トークン取得
            jwt_token = self._generate_jwt_token()
            
            # APNsペイロード構築
            payload = {
                "aps": {
                    "alert": {
                        "title": title,
                        "body": body
                    },
                    "sound": sound
                }
            }
            
            if badge is not None:
                payload["aps"]["badge"] = badge
            
            if data:
                payload.update(data)
            
            # HTTPリクエスト
            url = f"{self.apns_host}/3/device/{device_token}"
            headers = {
                "Authorization": f"bearer {jwt_token}",
                "apns-topic": self.bundle_id,
                "apns-push-type": "alert",
                "apns-priority": "10"
            }
            
            async with httpx.AsyncClient(http2=True) as client:
                response = await client.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=30.0
                )
            
            if response.status_code == 200:
                print(f"✅ 通知送信成功: {device_token[:20]}...")
                return {"success": True, "device_token": device_token}
            else:
                error_body = response.text
                print(f"❌ 通知送信失敗: {response.status_code} - {error_body}")
                return {
                    "success": False,
                    "device_token": device_token,
                    "status_code": response.status_code,
                    "error": error_body
                }
                
        except Exception as e:
            print(f"❌ 通知送信エラー: {e}")
            return {"success": False, "device_token": device_token, "error": str(e)}
    
    def send_notification_sync(
        self,
        device_token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        badge: Optional[int] = None,
        sound: str = "default"
    ) -> Dict[str, Any]:
        """
        同期版の通知送信（バックグラウンドタスク用）
        """
        if not self._is_configured():
            print("⚠️ APNsが設定されていません。通知をスキップします。")
            return {"success": False, "error": "APNs not configured"}
        
        try:
            import httpx
            
            # JWT認証トークン取得
            jwt_token = self._generate_jwt_token()
            
            # APNsペイロード構築
            payload = {
                "aps": {
                    "alert": {
                        "title": title,
                        "body": body
                    },
                    "sound": sound
                }
            }
            
            if badge is not None:
                payload["aps"]["badge"] = badge
            
            if data:
                payload.update(data)
            
            # HTTPリクエスト（同期版）
            url = f"{self.apns_host}/3/device/{device_token}"
            headers = {
                "Authorization": f"bearer {jwt_token}",
                "apns-topic": self.bundle_id,
                "apns-push-type": "alert",
                "apns-priority": "10"
            }
            
            with httpx.Client(http2=True) as client:
                response = client.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=30.0
                )
            
            if response.status_code == 200:
                print(f"✅ 通知送信成功: {device_token[:20]}...")
                return {"success": True, "device_token": device_token}
            else:
                error_body = response.text
                print(f"❌ 通知送信失敗: {response.status_code} - {error_body}")
                return {
                    "success": False,
                    "device_token": device_token,
                    "status_code": response.status_code,
                    "error": error_body
                }
                
        except Exception as e:
            print(f"❌ 通知送信エラー: {e}")
            return {"success": False, "device_token": device_token, "error": str(e)}
    
    def send_storybook_complete_notification(
        self,
        db: Session,
        user_id: str,
        storybook_id: int,
        storybook_title: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        絵本生成完了通知を送信
        
        Args:
            db: データベースセッション
            user_id: ユーザーID
            storybook_id: ストーリーブックID
            storybook_title: 絵本のタイトル（オプション）
        
        Returns:
            各デバイスへの送信結果リスト
        """
        # ユーザーのデバイストークンを取得
        device_tokens = db.query(DeviceToken).filter(
            DeviceToken.user_id == user_id
        ).all()
        
        if not device_tokens:
            print(f"⚠️ ユーザー {user_id} のデバイストークンがありません")
            return []
        
        # 通知内容
        title = "えほんができたよ！🎉"
        body = storybook_title if storybook_title else "絵本が完成しました！見てみましょう"
        
        # カスタムデータ（アプリで絵本を開くため）
        custom_data = {
            "storybook_id": storybook_id,
            "action": "view_storybook"
        }
        
        results = []
        for dt in device_tokens:
            result = self.send_notification_sync(
                device_token=dt.device_token,
                title=title,
                body=body,
                data=custom_data
            )
            results.append(result)
        
        print(f"📬 通知送信完了: {len(results)}件（成功: {sum(1 for r in results if r.get('success'))}件）")
        return results


# グローバルインスタンス（シングルトン）
push_notification_service = PushNotificationService()
