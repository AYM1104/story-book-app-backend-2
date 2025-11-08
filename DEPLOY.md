# Cloud Run デプロイ手順（簡易版）

このドキュメントでは、バックエンドをCloud Runにデプロイする簡単な手順を説明します。

## 前提条件

1. Google Cloud Platformアカウント
2. Google Cloud CLI（gcloud）のインストールと設定
3. 必要なAPIキーと認証情報

## デプロイ方法

### 方法1: GitHub Actionsを使用（推奨・自動デプロイ）

このプロジェクトはGitHub Actionsと連携しており、`main`ブランチにプッシュすると自動的にCloud Runにデプロイされます。

#### 初回設定

1. **GitHub Secretsの設定**
   - GitHubリポジトリの「Settings」→「Secrets and variables」→「Actions」に移動
   - `GCP_SA_KEY`という名前でサービスアカウントキー（JSON形式）を追加

2. **Secret Managerに環境変数を設定**
   ```bash
   # スクリプトに実行権限を付与
   chmod +x setup-secrets.sh
   
   # スクリプトを実行して対話形式で設定
   ./setup-secrets.sh
   ```

3. **サービスアカウントへの権限付与**
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

#### デプロイの実行

`main`ブランチにプッシュするだけで自動的にデプロイされます：

```bash
git add .
git commit -m "Update backend"
git push origin main
```

デプロイの進行状況はGitHub Actionsのページで確認できます。

### 方法2: 手動デプロイ

#### 1. Google Cloudプロジェクトの設定

```bash
# Google Cloudにログイン
gcloud auth login

# プロジェクトを設定
gcloud config set project YOUR_PROJECT_ID
```

### 2. Secret Managerに環境変数を設定

機密情報を安全に管理するため、Google Cloud Secret Managerを使用します。

```bash
# スクリプトに実行権限を付与
chmod +x setup-secrets.sh

# スクリプトを実行して対話形式で設定
./setup-secrets.sh
```

**必須の環境変数:**
- `SUPABASE_URL` - SupabaseプロジェクトのURL
- `SUPABASE_ANON_KEY` - Supabase匿名キー
- `SUPABASE_DB_URL` - Supabaseデータベース接続URL
- `GEMINI_API_KEY` - Google Gemini APIキー
- `GCS_BUCKET_NAME` - Google Cloud Storageバケット名

**推奨の環境変数:**
- `SUPABASE_SERVICE_ROLE_KEY` - Supabaseサービスロールキー
- `GOOGLE_API_KEY` - Google APIキー

### 3. サービスアカウントへの権限付与

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

### 4. デプロイの実行

```bash
# スクリプトに実行権限を付与
chmod +x deploy.sh

# デプロイを実行
./deploy.sh
```

デプロイスクリプトは以下を自動的に実行します：
- 必要なAPIの有効化
- Secret Managerの設定確認
- Cloud Buildによるビルドとデプロイ
- ヘルスチェック

### 5. デプロイ後の確認

```bash
# サービスのURLを確認
gcloud run services describe ehonnotane-backend --region=us-west1 --format='value(status.url)'

# ログを確認
gcloud run services logs read ehonnotane-backend --region=us-west1 --limit=50

# ヘルスチェック
curl https://YOUR_SERVICE_URL/health
```

## トラブルシューティング

### Secret Managerのシークレットが設定されていない

```bash
# シークレットの一覧を確認
gcloud secrets list

# シークレットを再設定
./setup-secrets.sh
```

**現在のバックエンドURL**: https://ehonnotane-backend-20459204449.us-west1.run.app

### デプロイが失敗する

**GitHub Actionsの場合:**
- GitHub Actionsのログを確認
- `GCP_SA_KEY`が正しく設定されているか確認
- Secret Managerのシークレットが設定されているか確認

**手動デプロイの場合:**
```bash
# ビルドログを確認
gcloud builds list --limit=1
gcloud builds log BUILD_ID

# Cloud Runのログを確認
gcloud run services logs read ehonnotane-backend --region=us-west1
```

### 環境変数が正しく設定されていない

```bash
# 環境変数を確認
gcloud run services describe ehonnotane-backend --region=us-west1 --format='value(spec.template.spec.containers[0].env)'

# 環境変数を直接設定する場合（推奨はSecret Managerを使用）
gcloud run services update ehonnotane-backend \
  --region=us-west1 \
  --set-env-vars="KEY=VALUE"
```

## 更新とロールバック

### サービスの更新

**GitHub Actionsを使用する場合:**
`main`ブランチにプッシュするだけで自動的に更新されます。

**手動で更新する場合:**
コードを変更した後、再度デプロイを実行：

```bash
./deploy.sh
```

### ロールバック

以前のリビジョンに戻す：

```bash
# リビジョンの一覧を確認
gcloud run revisions list --service=ehonnotane-backend --region=us-west1

# 特定のリビジョンにトラフィックを戻す
gcloud run services update-traffic ehonnotane-backend \
  --to-revisions=REVISION_NAME=100 \
  --region=us-west1
```

## 詳細情報

より詳細な情報については、`CLOUD_RUN_DEPLOYMENT.md`を参照してください。

