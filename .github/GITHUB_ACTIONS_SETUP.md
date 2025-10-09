# GitHub Actions 自動デプロイ設定手順

このドキュメントでは、GitHubにプッシュしたら自動的にCloud Runにデプロイされるように設定する手順を説明します。

## 前提条件

1. Google Cloud Platform プロジェクト
2. Cloud Run と Cloud Build API が有効化されていること
3. GitHubリポジトリへのアクセス権限

## 手順

### 1. GCP サービスアカウントの作成

```bash
# サービスアカウントを作成
gcloud iam service-accounts create github-actions \
  --display-name="GitHub Actions Deployer"

# プロジェクトIDを環境変数に設定
export PROJECT_ID=$(gcloud config get-value project)

# 必要な権限を付与
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/cloudbuild.builds.editor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"
```

### 2. サービスアカウントキーの作成

```bash
# JSONキーファイルを作成
gcloud iam service-accounts keys create ~/github-actions-key.json \
  --iam-account=github-actions@${PROJECT_ID}.iam.gserviceaccount.com

# 作成されたキーの内容を表示（コピーして使用）
cat ~/github-actions-key.json
```

⚠️ **重要**: このJSONキーは一度しか表示されません。安全に保管してください。

### 3. GitHub Secrets の設定

GitHubリポジトリの設定画面で以下のSecretsを追加します：

1. リポジトリページにアクセス
2. `Settings` → `Secrets and variables` → `Actions` に移動
3. `New repository secret` をクリック

#### 設定が必要なSecrets:

| Secret名 | 説明 | 取得方法 |
|---------|------|---------|
| `GCP_SA_KEY` | サービスアカウントのJSONキー | 上記で作成した `github-actions-key.json` の内容全体をコピー |
| `GCP_PROJECT_ID` | GCPプロジェクトID | `gcloud config get-value project` で確認 |

### 4. ワークフローの動作

設定完了後、以下のタイミングで自動デプロイが実行されます：

- `master` ブランチに `backend/` 配下のファイルがプッシュされたとき
- `.github/workflows/deploy-backend.yml` が変更されたとき

### 5. デプロイの確認

1. GitHubリポジトリの `Actions` タブでワークフローの実行状況を確認
2. 成功すると、Cloud Runに新しいリビジョンがデプロイされます

```bash
# デプロイされたサービスを確認
gcloud run services list --region=asia-northeast1

# ログを確認
gcloud run services logs read story-book-backend --region=asia-northeast1
```

### 6. トラブルシューティング

#### エラー: Permission denied

サービスアカウントに必要な権限が付与されていない可能性があります。手順1の権限付与を再度実行してください。

#### エラー: API not enabled

必要なAPIを有効化します：

```bash
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

#### ワークフローが実行されない

- `backend/` ディレクトリ配下のファイルが変更されているか確認
- `master` ブランチにプッシュされているか確認

## セキュリティ上の注意

1. サービスアカウントキーは絶対にリポジトリにコミットしないでください
2. GitHub Secretsに保存したキーは暗号化されて保存されます
3. 不要になったサービスアカウントキーは削除してください：

```bash
# キーのリストを表示
gcloud iam service-accounts keys list \
  --iam-account=github-actions@${PROJECT_ID}.iam.gserviceaccount.com

# キーを削除
gcloud iam service-accounts keys delete KEY_ID \
  --iam-account=github-actions@${PROJECT_ID}.iam.gserviceaccount.com
```

## 追加の設定（オプション）

### 環境変数の設定

Cloud Runの環境変数は、`cloudbuild.yaml` またはコンソールで設定できます：

```bash
gcloud run services update story-book-backend \
  --region=asia-northeast1 \
  --set-env-vars="ENV_VAR_NAME=value"
```

### 通知の設定

デプロイの成功/失敗をSlackなどに通知したい場合は、ワークフローファイルに通知ステップを追加できます。

