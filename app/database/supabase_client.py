from supabase import create_client, Client
from app.core.supabase_config import SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY, validate_supabase_config
import os
from typing import Optional

# Supabase設定の検証
try:
    validate_supabase_config()
except ValueError as e:
    print(f"Supabase設定エラー: {e}")
    print("環境変数を確認してください")

class SupabaseClient:
    """Supabaseクライアントのラッパークラス"""
    
    def __init__(self):
        self._anon_client: Optional[Client] = None
        self._service_client: Optional[Client] = None
    
    @property
    def anon_client(self) -> Client:
        """匿名ユーザー用のSupabaseクライアント"""
        if self._anon_client is None:
            self._anon_client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        return self._anon_client
    
    @property
    def service_client(self) -> Client:
        """サービスロール用のSupabaseクライアント（管理者権限）"""
        if self._service_client is None:
            if not SUPABASE_SERVICE_ROLE_KEY:
                raise ValueError("SUPABASE_SERVICE_ROLE_KEYが設定されていません")
            self._service_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        return self._service_client
    
    def get_client(self, use_service_role: bool = False) -> Client:
        """Supabaseクライアントを取得
        
        Args:
            use_service_role: Trueの場合はサービスロールクライアントを返す
        
        Returns:
            Supabaseクライアント
        """
        if use_service_role:
            return self.service_client
        return self.anon_client

# グローバルインスタンス
supabase_client = SupabaseClient()

def get_supabase_client(use_service_role: bool = False) -> Client:
    """Supabaseクライアントを取得する関数
    
    Args:
        use_service_role: Trueの場合はサービスロールクライアントを返す
    
    Returns:
        Supabaseクライアント
    """
    return supabase_client.get_client(use_service_role)

# テスト用の関数
def test_supabase_connection():
    """Supabase接続をテスト"""
    try:
        client = get_supabase_client()
        # 簡単なクエリで接続をテスト
        result = client.table("_test").select("*").limit(1).execute()
        print("✅ Supabase接続成功")
        return True
    except Exception as e:
        print(f"❌ Supabase接続エラー: {e}")
        return False
