# Supabase統合ガイド

このプロジェクトでは、Supabaseをデータベースとして使用するための設定が含まれています。

## 作成されたファイル

### 設定ファイル
- `app/core/supabase_config.py` - Supabase設定管理
- `app/database/supabase_session.py` - Supabase用SQLAlchemyセッション
- `app/database/supabase_base.py` - Supabase用ベースモデル
- `app/database/supabase_client.py` - Supabaseクライアント

### 環境変数
- `SUPABASE_ENV_EXAMPLE.txt` - 環境変数の例

## セットアップ手順

### 1. Supabaseプロジェクトの作成
1. [Supabase](https://supabase.com)でアカウントを作成
2. 新しいプロジェクトを作成
3. プロジェクトのURLとAPIキーを取得

### 2. 環境変数の設定
```bash
# SUPABASE_ENV_EXAMPLE.txtを参考に.envファイルを作成
cp SUPABASE_ENV_EXAMPLE.txt .env
```

必要な環境変数：
- `SUPABASE_URL` - プロジェクトURL
- `SUPABASE_ANON_KEY` - 匿名キー
- `SUPABASE_SERVICE_ROLE_KEY` - サービスロールキー
- `SUPABASE_DB_URL` - PostgreSQL接続URL

### 3. 依存関係のインストール
```bash
pip install -r requirements.txt
```

### 4. データベース接続のテスト
```python
# Pythonでテスト
from app.database.supabase_session import test_supabase_connection
from app.database.supabase_client import test_supabase_connection

# SQLAlchemy接続テスト
test_supabase_connection()

# Supabaseクライアント接続テスト
test_supabase_connection()
```

## 使用方法

### SQLAlchemyモデルの作成
```python
from app.database.supabase_base import SupabaseBase
from sqlalchemy import Column, Integer, String

class User(SupabaseBase):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
```

### データベースセッションの使用
```python
from app.database.supabase_session import get_supabase_db

# FastAPIの依存性注入で使用
@app.get("/users")
def get_users(db: Session = Depends(get_supabase_db)):
    return db.query(User).all()
```

### Supabaseクライアントの使用
```python
from app.database.supabase_client import get_supabase_client

# 匿名ユーザー用クライアント
client = get_supabase_client()

# サービスロール用クライアント（管理者権限）
admin_client = get_supabase_client(use_service_role=True)

# データの取得
result = client.table("users").select("*").execute()
```

## 既存ファイルとの関係

- 既存の`session.py`、`base.py`はそのまま残されています
- 新しいSupabase用ファイルは`supabase_`プレフィックスで区別されています
- 必要に応じて既存ファイルから新しいファイルに移行できます

## 注意事項

- サービスロールキーは秘密に保持してください
- 本番環境では適切なRLS（Row Level Security）ポリシーを設定してください
- ストレージを使用する場合は、適切なバケットポリシーを設定してください
