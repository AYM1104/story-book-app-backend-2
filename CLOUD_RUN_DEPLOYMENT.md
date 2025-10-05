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

### 2. 環境変数の設定

`cloud-run-env-example.txt`を参考に、必要な環境変数を設定します：

```bash
# Cloud Runサービスに環境変数を設定
gcloud run services update story-book-backend \
  --region=asia-northeast1 \
  --set-env-vars="GEMINI_API_KEY=your_key,GOOGLE_API_KEY=your_key,GCS_BUCKET_NAME=your_bucket,SUPABASE_URL=your_url,SUPABASE_KEY=your_key,STORAGE_TYPE=gcs"
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

1. **メモリ不足エラー**
   - `--memory`パラメータを増やす（例：4Gi）

2. **タイムアウトエラー**
   - `--timeout`パラメータを増やす（例：300s）

3. **環境変数の設定漏れ**
   - 必要な環境変数がすべて設定されているか確認

4. **権限エラー**
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
