# バックグラウンド絵本生成機能 - デプロイ手順

Cloud Tasksを使用したバックグラウンド処理をデプロイするための手順書です。

## 前提条件

- GCPプロジェクトが作成済み
- Cloud Runサービス `ehonnotane-backend` がデプロイ済み
- `gcloud` CLIがインストール済み

---

## ステップ1: Cloud Tasksキューの作成

```bash
# 環境変数を設定
export PROJECT_ID="ayu1104"  # .envから取得
export REGION="us-west1"     # Cloud Runと同じリージョン
export QUEUE_NAME="image-generation-queue"

# GCPプロジェクトを設定
gcloud config set project $PROJECT_ID

# Cloud Tasksキューを作成
gcloud tasks queues create $QUEUE_NAME \
  --location=$REGION \
  --max-attempts=3 \
  --max-retry-duration=7200s \
  --max-concurrent-dispatches=10

# 作成されたキューを確認
gcloud tasks queues describe $QUEUE_NAME --location=$REGION
```

---

## ステップ2: 環境変数の設定

### Secret Managerに環境変数を追加

```bash
# BACKEND_URLをSecret Managerに追加
echo "https://ehonnotane-backend-877241552096.us-west1.run.app" | \
  gcloud secrets create BACKEND_URL --data-file=-

# または、既存のシークレットを更新
echo "https://ehonnotane-backend-877241552096.us-west1.run.app" | \
  gcloud secrets versions add BACKEND_URL --data-file=-
```

### cloudbuild.yamlの更新

`cloudbuild.yaml`の`--set-secrets`行に`BACKEND_URL`を追加:

```yaml
- '--set-secrets'
- 'SUPABASE_URL=SUPABASE_URL:latest,SUPABASE_ANON_KEY=SUPABASE_ANON_KEY:latest,SUPABASE_DB_URL=SUPABASE_DB_URL:latest,GOOGLE_API_KEY_Free=GOOGLE_API_KEY_Free:latest,GOOGLE_API_KEY_Paid=GOOGLE_API_KEY_Paid:latest,GCS_BUCKET_NAME=GCS_BUCKET_NAME:latest,SUPABASE_SERVICE_ROLE_KEY=SUPABASE_SERVICE_ROLE_KEY:latest,AUTH0_DOMAIN=AUTH0_DOMAIN:latest,AUTH0_API_AUDIENCE=AUTH0_API_AUDIENCE:latest,AUTH0_NATIVE_CLIENT_ID=AUTH0_NATIVE_CLIENT_ID:latest,BACKEND_URL=BACKEND_URL:latest'
```

または、デプロイ時に環境変数として設定:

```yaml
- '--set-env-vars'
- 'STORAGE_TYPE=gcs,CLOUD_TASKS_LOCATION=us-west1,CLOUD_TASKS_QUEUE=image-generation-queue'
```

---

## ステップ3: サービスアカウントの権限設定

```bash
# サービスアカウント名を設定
export SERVICE_ACCOUNT="ehonnotane-backend-sa@$PROJECT_ID.iam.gserviceaccount.com"

# 1. Cloud Run Invoker権限を付与（Cloud TasksがCloud Runを呼び出すため）
gcloud run services add-iam-policy-binding ehonnotane-backend \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/run.invoker" \
  --region=$REGION

# 2. Cloud Tasks管理者権限を付与（タスクの作成・削除のため）
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/cloudtasks.admin"

# 権限を確認
gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:$SERVICE_ACCOUNT"
```

---

## ステップ4: 依存関係のインストール（ローカルテスト用）

```bash
cd /Users/ayu/create/native_app/ehonnotane/backend

# 仮想環境を有効化（存在する場合）
source venv/bin/activate

# 依存関係をインストール
pip install -r requirements.txt

# Cloud Tasks SDKが正しくインストールされたか確認
python -c "from google.cloud import tasks_v2; print('✅ Cloud Tasks SDK installed')"
```

---

## ステップ5: ローカルテスト（オプション）

```bash
# バックエンドをローカルで起動
uvicorn app.main:app --reload --port 8080

# 別のターミナルで、タスクWebhookエンドポイントをテスト
curl -X POST http://localhost:8080/api/tasks/image-generation \
  -H "Content-Type: application/json" \
  -H "User-Agent: Google-Cloud-Tasks" \
  -d '{
    "storybook_id": 1,
    "story_plot_id": 1,
    "reference_image_path": "https://storage.googleapis.com/ehonnotane-images-storage/test.jpg",
    "strength": 0.85,
    "prefix": "",
    "user_id": "auth0|123456",
    "story_pages": 5
  }'
```

---

## ステップ6: Cloud Runにデプロイ

```bash
cd /Users/ayu/create/native_app/ehonnotane/backend

# Cloud Buildを使用してデプロイ
gcloud builds submit --config cloudbuild.yaml

# デプロイが完了したら、サービスを確認
gcloud run services describe ehonnotane-backend --region=$REGION
```

---

## ステップ7: 動作確認

### 1. ヘルスチェック

```bash
# バックエンドのヘルスチェック
curl https://ehonnotane-backend-877241552096.us-west1.run.app/health

# タスクWebhookのヘルスチェック
curl https://ehonnotane-backend-877241552096.us-west1.run.app/api/tasks/health
```

### 2. エンドツーエンドテスト

iOSアプリから絵本を生成:

1. アプリで新しい絵本を作成
2. テーマを選択
3. 画像生成を開始
4. **アプリを完全に閉じる**
5. 5分後にアプリを再度開く
6. 本棚で絵本を確認 → 画像が生成されているはず

### 3. Cloud Tasksのモニタリング

```bash
# タスクキューの状態を確認
gcloud tasks queues describe $QUEUE_NAME --location=$REGION

# 実行中のタスクをリスト表示
gcloud tasks list --queue=$QUEUE_NAME --location=$REGION
```

Cloud Consoleでモニタリング:
https://console.cloud.google.com/cloudtasks/queue/$REGION/$QUEUE_NAME?project=$PROJECT_ID

---

## トラブルシューティング

### エラー: "Queue not found"

```bash
# キューが作成されているか確認
gcloud tasks queues list --location=$REGION

# なければ作成
gcloud tasks queues create $QUEUE_NAME --location=$REGION
```

### エラー: "Permission denied"

```bash
# サービスアカウントの権限を再確認
gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:ehonnotane-backend-sa@$PROJECT_ID.iam.gserviceaccount.com"

# 必要な権限を再付与
# （ステップ3を参照）
```

### エラー: "Module 'google.cloud.tasks' not found"

```bash
# requirements.txtに google-cloud-tasks が含まれているか確認
grep google-cloud-tasks requirements.txt

# 再デプロイ
gcloud builds submit --config cloudbuild.yaml
```

### Cloud Tasksのログを確認

```bash
# Cloud Logsでタスクの実行ログを確認
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=ehonnotane-backend AND textPayload:\"画像生成タスク\"" \
  --limit 50 \
  --format json
```

---

## ロールバック手順

問題が発生した場合、以前のバージョンにロールバック:

```bash
# リビジョンをリスト表示
gcloud run revisions list --service=ehonnotane-backend --region=$REGION

# 特定のリビジョンにロールバック
gcloud run services update-traffic ehonnotane-backend \
  --to-revisions=REVISION_NAME=100 \
  --region=$REGION
```

---

## まとめ

✅ Cloud Tasksキューを作成  
✅ 環境変数を設定  
✅ サービスアカウントの権限を設定  
✅ Cloud Runにデプロイ  
✅ 動作確認とモニタリング

これで、絵本生成がバックグラウンドで確実に実行されるようになりました！
