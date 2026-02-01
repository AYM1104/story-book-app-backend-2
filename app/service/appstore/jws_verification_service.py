"""
App Store JWS (JSON Web Signature) 検証サービス

App StoreからのトランザクションデータとServer Notificationsは
JWSで署名されており、このサービスでその真正性を検証します。
"""

import jwt
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import logging

logger = logging.getLogger(__name__)


class JWSVerificationService:
    """App Store JWS検証サービス"""
    
    # App Store公開鍵エンドポイント
    APPLE_PUBLIC_KEYS_URL = "https://appleid.apple.com/auth/keys"
    
    # 公開鍵のキャッシュ（24時間）
    _public_keys_cache: Optional[Dict[str, Any]] = None
    _cache_timestamp: Optional[datetime] = None
    _CACHE_DURATION = timedelta(hours=24)
    
    @classmethod
    def verify_jws(cls, jws_token: str) -> Dict[str, Any]:
        """
        JWSトークンを検証してペイロードを返す
        
        Args:
            jws_token: JWS形式のトークン文字列
            
        Returns:
            デコードされたペイロード (dict)
            
        Raises:
            ValueError: JWS検証失敗時
        """
        try:
            # JWSヘッダーをデコード（検証なし）
            unverified_header = jwt.get_unverified_header(jws_token)
            kid = unverified_header.get("kid")
            
            if not kid:
                raise ValueError("JWSヘッダーにkid（Key ID）が含まれていません")
            
            # 公開鍵を取得
            public_key = cls._get_public_key(kid)
            
            if not public_key:
                # キャッシュをクリアして再取得
                cls._clear_cache()
                public_key = cls._get_public_key(kid)
                
                if not public_key:
                    raise ValueError(f"公開鍵が見つかりません: kid={kid}")
            
            # JWSを検証してデコード
            payload = jwt.decode(
                jws_token,
                public_key,
                algorithms=["ES256"],  # App StoreはES256を使用
                options={
                    "verify_signature": True,
                    "verify_exp": True,  # 有効期限を検証
                    "verify_iat": True,  # 発行日時を検証
                }
            )
            
            logger.info(f"✅ JWS検証成功: kid={kid}")
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.error("❌ JWSの有効期限が切れています")
            raise ValueError("JWSの有効期限が切れています")
            
        except jwt.InvalidSignatureError:
            logger.error("❌ JWS署名が無効です")
            raise ValueError("JWS署名が無効です")
            
        except Exception as e:
            logger.error(f"❌ JWS検証エラー: {str(e)}")
            raise ValueError(f"JWS検証エラー: {str(e)}")
    
    @classmethod
    def _get_public_key(cls, kid: str) -> Optional[str]:
        """
        Key IDに対応する公開鍵を取得
        
        Args:
            kid: Key ID
            
        Returns:
            PEM形式の公開鍵文字列、見つからない場合はNone
        """
        # キャッシュから取得
        keys = cls._get_cached_public_keys()
        
        if not keys:
            return None
        
        # kidに一致する鍵を探す
        for key_data in keys.get("keys", []):
            if key_data.get("kid") == kid:
                return cls._jwk_to_pem(key_data)
        
        return None
    
    @classmethod
    def _get_cached_public_keys(cls) -> Optional[Dict[str, Any]]:
        """
        公開鍵をキャッシュから取得、期限切れの場合は再取得
        
        Returns:
            公開鍵データ (JWKS形式)
        """
        now = datetime.utcnow()
        
        # キャッシュが有効かチェック
        if (cls._public_keys_cache is not None and 
            cls._cache_timestamp is not None and
            now - cls._cache_timestamp < cls._CACHE_DURATION):
            logger.debug("📦 公開鍵をキャッシュから取得")
            return cls._public_keys_cache
        
        # キャッシュが無効 or 存在しない場合は再取得
        try:
            logger.info(f"🔄 App Store公開鍵を取得中: {cls.APPLE_PUBLIC_KEYS_URL}")
            response = requests.get(cls.APPLE_PUBLIC_KEYS_URL, timeout=10)
            response.raise_for_status()
            
            keys_data = response.json()
            
            # キャッシュに保存
            cls._public_keys_cache = keys_data
            cls._cache_timestamp = now
            
            logger.info(f"✅ 公開鍵を取得しました: {len(keys_data.get('keys', []))}個")
            return keys_data
            
        except Exception as e:
            logger.error(f"❌ 公開鍵の取得に失敗: {str(e)}")
            return None
    
    @classmethod
    def _clear_cache(cls):
        """公開鍵キャッシュをクリア"""
        logger.info("🗑️ 公開鍵キャッシュをクリアしました")
        cls._public_keys_cache = None
        cls._cache_timestamp = None
    
    @classmethod
    def _jwk_to_pem(cls, jwk: Dict[str, Any]) -> str:
        """
        JWK (JSON Web Key) をPEM形式に変換
        
        Args:
            jwk: JWK形式の鍵データ
            
        Returns:
            PEM形式の公開鍵文字列
        """
        try:
            from cryptography.hazmat.primitives.asymmetric import ec
            from cryptography.hazmat.primitives.serialization import (
                Encoding, PublicFormat
            )
            import base64
            
            # JWKからxとy座標を取得
            x_bytes = base64.urlsafe_b64decode(jwk["x"] + "==")
            y_bytes = base64.urlsafe_b64decode(jwk["y"] + "==")
            
            # 曲線名を取得 (通常はP-256)
            curve_name = jwk.get("crv", "P-256")
            if curve_name == "P-256":
                curve = ec.SECP256R1()
            else:
                raise ValueError(f"サポートされていない曲線: {curve_name}")
            
            # ECポイントから公開鍵を構築
            x = int.from_bytes(x_bytes, byteorder='big')
            y = int.from_bytes(y_bytes, byteorder='big')
            
            public_numbers = ec.EllipticCurvePublicNumbers(x, y, curve)
            public_key = public_numbers.public_key(default_backend())
            
            # PEM形式にエンコード
            pem = public_key.public_bytes(
                encoding=Encoding.PEM,
                format=PublicFormat.SubjectPublicKeyInfo
            )
            
            return pem.decode('utf-8')
            
        except Exception as e:
            logger.error(f"❌ JWKからPEMへの変換エラー: {str(e)}")
            raise ValueError(f"JWKからPEMへの変換に失敗: {str(e)}")


# 使用例
if __name__ == "__main__":
    # テスト用（実際のJWSトークンで検証）
    import sys
    
    if len(sys.argv) > 1:
        jws_token = sys.argv[1]
        try:
            payload = JWSVerificationService.verify_jws(jws_token)
            print("✅ 検証成功！")
            print("ペイロード:")
            import json
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        except ValueError as e:
            print(f"❌ 検証失敗: {e}")
    else:
        print("使用方法: python jws_verification_service.py <JWSトークン>")
