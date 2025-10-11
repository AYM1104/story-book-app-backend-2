# Cloud Run デプロイ クイックスタートガイド

このガイドでは、最短でStory Book AppのバックエンドをGoogle Cloud Runにデプロイする手順を説明します。

## 前提条件

- Google Cloud Platformアカウント
- Google Cloud CLI（gcloud）がインストール済み
- Supabaseプロジェクトが作成済み

## 手順（約10分）

### 1. Google Cloudにログイン

```bash
# Google Cloudにログイン
gcloud auth login

# プロジェクトを設定（YOUR_PROJECT_IDを実際のプロジェクトIDに置き換え）
gcloud config set project YOUR_PROJECT_ID
```

### 2. 必要なAPIを有効化

```bash
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable secretmanager.googleapis.com
```

### 3. GCSバケットへの権限を設定

Cloud Runサービスアカウントに、GCSバケットへのアクセス権限を付与します：

```bash
# プロジェクトIDとプロジェクト番号を取得
PROJECT_ID=$(gcloud config get-value project)
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')

# Cloud Runサービスアカウントに権限を付与
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member=serviceAccount:$PROJECT_NUMBER-compute@developer.gserviceaccount.com \
  --role=roles/storage.objectAdmin
```

### 4. 初回デプロイを実行

まず、環境変数なしでCloud Runサービスを作成します：

```bash
# Cloud Buildでビルドとデプロイを実行
gcloud builds submit --config cloudbuild.yaml .
```

デプロイには5〜10分程度かかります。

### 5. 環境変数を設定

デプロイが完了したら、環境変数を設定します：

```bash
# スクリプトを実行して対話形式で環境変数を設定
./set-cloudrun-env.sh
```

以下の情報を用意してください：

**【必須】5つ**
- **SUPABASE_URL**: `https://xxxxxxxxxxxx.supabase.co`
  - Supabaseダッシュボードの「Settings > API > Project URL」から取得
- **SUPABASE_ANON_KEY**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`
  - Supabaseダッシュボードの「Settings > API > Project API keys > anon public」から取得
- **SUPABASE_DB_URL**: `postgresql://postgres:[PASSWORD]@db.xxxxxxxxxxxx.supabase.co:5432/postgres`
  - Supabaseダッシュボードの「Settings > Database > Connection string」から取得
- **GEMINI_API_KEY**: `AIzaSy...`
  - Google AI Studio (https://aistudio.google.com/app/apikey) から取得
- **GCS_BUCKET_NAME**: `your-bucket-name`
  - Google Cloud Consoleの「Cloud Storage > バケット」から既存のバケット名を確認

**【推奨】1つ**
- **SUPABASE_SERVICE_ROLE_KEY**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`
  - Supabaseダッシュボードの「Settings > API > Project API keys > service_role secret」から取得
  - データベースの管理操作に必要

環境変数を設定すると、Cloud Runサービスが自動的に再起動され、新しい設定が反映されます。

**💡 システム構成:**
- データベース: Supabase (PostgreSQL)
- 画像ストレージ: Google Cloud Storage
- AI生成: Google Gemini

### 6. 動作確認

```bash
# サービス一覧を確認
gcloud run services list

# URLを取得
gcloud run services describe story-book-backend \
  --region=asia-northeast1 \
  --format='value(status.url)'
```

表示されたURLにアクセスして、APIが正常に動作していることを確認してください。

## トラブルシューティング

### エラーが発生した場合

```bash
# ログを確認
gcloud run services logs read story-book-backend --region=asia-northeast1 --limit=50

# サービスの詳細を確認
gcloud run services describe story-book-backend --region=asia-northeast1
```

### よくあるエラー

1. **環境変数が設定されていない**
   ```bash
   # シークレットが作成されているか確認
   gcloud secrets list
   ```

2. **権限エラー**
   ```bash
   # IAMポリシーを確認
   gcloud projects get-iam-policy $PROJECT_ID
   ```

3. **ビルドエラー**
   ```bash
   # ビルドログを確認
   gcloud builds list --limit=5
   gcloud builds log <BUILD_ID>
   ```

## 更新とメンテナンス

### コードを更新してデプロイ

```bash
# 変更をコミット
git add .
git commit -m "Update backend"

# 再デプロイ
gcloud builds submit --config cloudbuild.yaml .
```

### 環境変数を更新

```bash
# 再度スクリプトを実行（環境変数が更新されます）
./set-cloudrun-env.sh
```

### サービスを削除

```bash
# Cloud Runサービスを削除（環境変数も一緒に削除されます）
gcloud run services delete story-book-backend --region=asia-northeast1
```

## サポート

詳細なドキュメントは `CLOUD_RUN_DEPLOYMENT.md` を参照してください。

