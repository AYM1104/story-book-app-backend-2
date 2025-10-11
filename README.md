# Story Book App Backend

AIを活用した絵本作成アプリケーションのバックエンドAPIです。

## 機能

- AI（Gemini）を使用したストーリー生成
- 画像生成とアップロード
- Supabaseとの統合
- Google Cloud Storage対応

## クイックスタート

### ローカル開発

```bash
# 仮想環境を有効化
source venv/bin/activate  # Windowsの場合: venv\Scripts\activate

# 依存関係をインストール
pip install -r requirements.txt

# 環境変数を設定（.envファイルを作成）
cp SUPABASE_ENV_EXAMPLE.txt .env
# .envファイルを編集して実際の値を設定

# アプリケーションを起動
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Cloud Runへのデプロイ

**最短10分でデプロイできます！**

詳細は以下のドキュメントを参照してください：

- 📖 **[クイックスタートガイド](QUICK_START_DEPLOY.md)** - 初めての方はこちら
- 📚 **[詳細デプロイガイド](CLOUD_RUN_DEPLOYMENT.md)** - より詳しい説明

### 簡単な手順

```bash
# 1. GCSバケットへの権限を設定
PROJECT_ID=$(gcloud config get-value project)
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member=serviceAccount:$PROJECT_NUMBER-compute@developer.gserviceaccount.com \
  --role=roles/storage.objectAdmin

# 2. 初回デプロイ
gcloud builds submit --config cloudbuild.yaml .

# 3. 環境変数を設定（対話形式）
./set-cloudrun-env.sh

# 完了！サービスが自動的に再起動され、環境変数が反映されます
```

**必要な環境変数（5つ）:**
- SUPABASE_URL（データベース）
- SUPABASE_ANON_KEY（データベース）
- SUPABASE_DB_URL（データベース）
- GEMINI_API_KEY（AI生成）
- GCS_BUCKET_NAME（画像ストレージ）

## トラブルシューティング

### Supabase設定エラー

```
Supabase設定エラー: 以下の環境変数が設定されていません: SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_DB_URL
```

または

```
❌ Failed to load image_generation_router: Expected string or URL object, got None
```

このエラーが発生した場合：

**原因**: Cloud Runに環境変数が設定されていない

**解決方法**:

1. 環境変数を設定（これだけでOK！）:
   ```bash
   ./set-cloudrun-env.sh
   ```

2. 設定が反映されているか確認:
   ```bash
   # Cloud Runサービスの環境変数を確認
   gcloud run services describe story-book-backend --region=asia-northeast1 --format=yaml | grep -A 20 "env:"
   ```

3. ログを確認:
   ```bash
   gcloud run services logs read story-book-backend --region=asia-northeast1 --limit=50
   ```

4. 正常に起動すると、以下のようなログが表示されます:
   ```
   ✅ データベース接続が正常に設定されました
   ✅ Supabase users router loaded successfully
   ✅ Image generation router loaded successfully
   ```

## ドキュメント

- [QUICK_START_DEPLOY.md](QUICK_START_DEPLOY.md) - Cloud Runへのデプロイクイックスタート
- [ENV_VARIABLES_GUIDE.md](ENV_VARIABLES_GUIDE.md) - 環境変数の完全ガイド（必須・任意の区別あり）
- [CLOUD_RUN_DEPLOYMENT.md](CLOUD_RUN_DEPLOYMENT.md) - Cloud Runデプロイの詳細ガイド
- [SUPABASE_README.md](SUPABASE_README.md) - Supabase設定ガイド
- [ENV_EXAMPLE.txt](ENV_EXAMPLE.txt) - 環境変数の例
- [SUPABASE_ENV_EXAMPLE.txt](SUPABASE_ENV_EXAMPLE.txt) - Supabase環境変数の例

## 技術スタック

- **フレームワーク**: FastAPI
- **言語**: Python 3.11
- **データベース**: Supabase (PostgreSQL)
- **画像ストレージ**: Google Cloud Storage
- **AI**: Google Gemini
- **デプロイ**: Google Cloud Run

## システム構成

```
┌─────────────┐
│  Frontend   │
└──────┬──────┘
       │
       ▼
┌─────────────────────────┐
│   Cloud Run (FastAPI)   │
│   ┌─────────────────┐   │
│   │  API Endpoints  │   │
│   └─────────────────┘   │
└───┬─────────┬─────────┬─┘
    │         │         │
    ▼         ▼         ▼
┌──────┐  ┌─────┐  ┌─────────┐
│ GCS  │  │ DB  │  │ Gemini  │
│(画像)│  │Supa │  │  API    │
│      │  │base │  │  (AI)   │
└──────┘  └─────┘  └─────────┘
```

## ライセンス

プライベートプロジェクト