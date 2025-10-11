# Google Cloud Run デプロイメント手順

このドキュメントでは、Story Book AppのバックエンドをGoogle Cloud Runにデプロイする手順を説明します。

## 前提条件

1. Google Cloud Platformアカウント
2. Google Cloud CLI（gcloud）のインストールと設定
3. Dockerのインストール（ローカルビルドの場合）
4. 必要なAPIキーとサービスアカウントの設定

## 手順

### 1. Google Cloudプロジェクトの設定

```bash
# Google Cloudにログイン
gcloud auth login

# プロジェクトを設定
gcloud config set project YOUR_PROJECT_ID

# 必要なAPIを有効化
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

### 2. Secret Managerへの環境変数の設定

機密情報を安全に管理するため、Google Cloud Secret Managerを使用します。

#### 方法1: スクリプトを使用（推奨）

```bash
# スクリプトに実行権限を付与
chmod +x setup-secrets.sh

# スクリプトを実行して対話形式で設定
./setup-secrets.sh
```

#### 方法2: 手動で設定

```bash
# Secret Manager APIを有効化
gcloud services enable secretmanager.googleapis.com

# 各シークレットを作成
echo "YOUR_SUPABASE_URL" | gcloud secrets create SUPABASE_URL --data-file=-
echo "YOUR_SUPABASE_ANON_KEY" | gcloud secrets create SUPABASE_ANON_KEY --data-file=-
echo "YOUR_SUPABASE_SERVICE_ROLE_KEY" | gcloud secrets create SUPABASE_SERVICE_ROLE_KEY --data-file=-
echo "YOUR_SUPABASE_DB_URL" | gcloud secrets create SUPABASE_DB_URL --data-file=-
echo "storybook-images" | gcloud secrets create SUPABASE_STORAGE_BUCKET --data-file=-
echo "YOUR_SUPABASE_JWT_SECRET" | gcloud secrets create SUPABASE_JWT_SECRET --data-file=-
echo "YOUR_GEMINI_API_KEY" | gcloud secrets create GEMINI_API_KEY --data-file=-
echo "YOUR_GOOGLE_API_KEY" | gcloud secrets create GOOGLE_API_KEY --data-file=-
echo "YOUR_GCS_BUCKET_NAME" | gcloud secrets create GCS_BUCKET_NAME --data-file=-
```

### 2.5. サービスアカウントへの権限付与

Secret Managerへのアクセス権限を付与します：

```bash
# プロジェクト番号を取得
PROJECT_ID=$(gcloud config get-value project)
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')

# Cloud Build サービスアカウントに権限を付与
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member=serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor

# Cloud Run サービスアカウントに権限を付与
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member=serviceAccount:$PROJECT_NUMBER-compute@developer.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor
```

### 3. デプロイ方法

#### 方法1: Cloud Buildを使用（推奨）

```bash
# プロジェクトルートから実行
cd backend

# Cloud Buildでビルドとデプロイを実行
gcloud builds submit --config cloudbuild.yaml .
```

#### 方法2: ローカルビルド

```bash
# Dockerイメージをビルド
docker build -t gcr.io/YOUR_PROJECT_ID/story-book-backend .

# Google Container Registryにプッシュ
docker push gcr.io/YOUR_PROJECT_ID/story-book-backend

# Cloud Runにデプロイ
gcloud run deploy story-book-backend \
  --image gcr.io/YOUR_PROJECT_ID/story-book-backend \
  --region asia-northeast1 \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --memory 2Gi \
  --cpu 2 \
  --max-instances 10
```

#### 方法3: ソースコードから直接デプロイ

```bash
gcloud run deploy story-book-backend \
  --source . \
  --region asia-northeast1 \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --memory 2Gi \
  --cpu 2 \
  --max-instances 10
```

### 4. デプロイ後の確認

```bash
# サービス一覧を確認
gcloud run services list

# ログを確認
gcloud run services logs read story-book-backend --region=asia-northeast1

# サービスの詳細を確認
gcloud run services describe story-book-backend --region=asia-northeast1
```

### 5. カスタムドメインの設定（オプション）

```bash
# カスタムドメインをマッピング
gcloud run domain-mappings create \
  --service story-book-backend \
  --domain your-domain.com \
  --region asia-northeast1
```

## トラブルシューティング

### よくある問題

1. **Supabase設定エラー: 環境変数が設定されていません**
   ```
   Supabase設定エラー: 以下の環境変数が設定されていません: SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_DB_URL
   ```
   
   **解決方法:**
   - Secret Managerにシークレットが正しく登録されているか確認:
     ```bash
     gcloud secrets list
     ```
   - サービスアカウントに`secretmanager.secretAccessor`ロールが付与されているか確認:
     ```bash
     PROJECT_ID=$(gcloud config get-value project)
     PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')
     gcloud projects get-iam-policy $PROJECT_ID \
       --flatten="bindings[].members" \
       --filter="bindings.members:serviceAccount:$PROJECT_NUMBER-compute@developer.gserviceaccount.com"
     ```
   - Cloud Runサービスの環境変数を確認:
     ```bash
     gcloud run services describe story-book-backend --region=asia-northeast1 --format=yaml
     ```

2. **メモリ不足エラー**
   - `--memory`パラメータを増やす（例：4Gi）

3. **タイムアウトエラー**
   - `--timeout`パラメータを増やす（例：300s）

4. **環境変数の設定漏れ**
   - 必要な環境変数がすべて設定されているか確認

5. **権限エラー**
   - サービスアカウントに適切な権限が付与されているか確認

### ログの確認

```bash
# リアルタイムログの確認
gcloud run services logs tail story-book-backend --region=asia-northeast1

# 特定の時間範囲のログ
gcloud run services logs read story-book-backend \
  --region=asia-northeast1 \
  --start-time="2024-01-01T00:00:00Z" \
  --end-time="2024-01-01T23:59:59Z"
```

## 更新とロールバック

### サービスの更新

```bash
# 新しいバージョンをデプロイ
gcloud run deploy story-book-backend \
  --image gcr.io/YOUR_PROJECT_ID/story-book-backend:new-tag \
  --region asia-northeast1
```

### ロールバック

```bash
# 以前のリビジョンに戻す
gcloud run services update-traffic story-book-backend \
  --to-revisions=REVISION_NAME=100 \
  --region asia-northeast1
```

## コスト最適化

1. **最小インスタンス数の設定**
   ```bash
   --min-instances 0  # リクエストがない時は0に設定
   ```

2. **最大インスタンス数の制限**
   ```bash
   --max-instances 5  # 必要に応じて調整
   ```

3. **CPU使用率の監視**
   - Google Cloud Consoleでメトリクスを確認

## セキュリティ設定

1. **認証の有効化**
   ```bash
   # 認証が必要な場合
   gcloud run services remove-iam-policy-binding story-book-backend \
     --member="allUsers" \
     --role="roles/run.invoker" \
     --region=asia-northeast1
   ```

2. **VPCコネクタの設定**（必要に応じて）
   ```bash
   --vpc-connector=projects/YOUR_PROJECT_ID/locations/asia-northeast1/connectors/YOUR_CONNECTOR
   ```
