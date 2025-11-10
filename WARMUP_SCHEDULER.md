# Cloud Run ウォームアップ設定ガイド

Cloud Runのコールドスタートを防ぐため、Cloud Schedulerを使って5分おきに`/health`エンドポイントにリクエストを送信する設定を行います。

## 概要

- **目的**: Cloud Runのコールドスタートによる初回ログイン失敗を防ぐ
- **方法**: Cloud Schedulerで5分おきに`/health`エンドポイントにアクセス
- **コスト**: 無料枠内（月8,640リクエスト程度、無料枠200万リクエストの0.4%）

## 設定手順

### 1. スクリプトの実行

バックエンドディレクトリで以下のコマンドを実行します：

```bash
cd storybook_backend/story-book-app-backend-2
./setup-warmup-scheduler.sh
```

### 2. スクリプトが実行すること

1. **必要なAPIの有効化**
   - Cloud Scheduler API
   - Cloud Run API

2. **サービスアカウントの作成**
   - 名前: `cloud-scheduler-invoker`
   - Cloud Runサービスを呼び出すための権限を持つ

3. **権限の付与**
   - Cloud Runサービスへの`roles/run.invoker`権限を付与

4. **Cloud Schedulerジョブの作成**
   - ジョブ名: `warmup-health-check`
   - スケジュール: 5分おき（`*/5 * * * *`）
   - ターゲット: `https://[SERVICE_URL]/health`
   - 認証: OIDC（サービスアカウントを使用）

## 確認方法

### ジョブの状態を確認

```bash
gcloud scheduler jobs describe warmup-health-check \
  --location=us-west1
```

### ジョブを手動で実行してテスト

```bash
gcloud scheduler jobs run warmup-health-check \
  --location=us-west1
```

### 実行履歴を確認

```bash
# Cloud Schedulerのログを確認
gcloud logging read "resource.type=cloud_scheduler_job AND resource.labels.job_id=warmup-health-check" \
  --limit=10 \
  --format=json
```

### Cloud Runのログでリクエストを確認

```bash
gcloud run services logs read ehonnotane-backend \
  --region=us-west1 \
  --limit=20
```

5分おきに`/health`へのリクエストが記録されていれば成功です。

## ジョブの管理

### ジョブを一時停止

```bash
gcloud scheduler jobs pause warmup-health-check \
  --location=us-west1
```

### ジョブを再開

```bash
gcloud scheduler jobs resume warmup-health-check \
  --location=us-west1
```

### ジョブを削除

```bash
gcloud scheduler jobs delete warmup-health-check \
  --location=us-west1
```

## トラブルシューティング

### ジョブが実行されない

1. **ジョブの状態を確認**
   ```bash
   gcloud scheduler jobs describe warmup-health-check --location=us-west1
   ```

2. **手動実行でテスト**
   ```bash
   gcloud scheduler jobs run warmup-health-check --location=us-west1
   ```

3. **エラーログを確認**
   ```bash
   gcloud logging read "resource.type=cloud_scheduler_job AND resource.labels.job_id=warmup-health-check AND severity>=ERROR" \
     --limit=10
   ```

### 権限エラーが発生する場合

サービスアカウントにCloud Run Invoker権限が付与されているか確認：

```bash
gcloud run services get-iam-policy ehonnotane-backend \
  --region=us-west1
```

権限がない場合は、スクリプトを再実行するか、手動で付与：

```bash
PROJECT_ID=$(gcloud config get-value project)
gcloud run services add-iam-policy-binding ehonnotane-backend \
  --region=us-west1 \
  --member="serviceAccount:cloud-scheduler-invoker@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/run.invoker"
```

## コストについて

- **Cloud Scheduler**: 月3ジョブまで無料、20,000回実行まで無料
- **Cloud Run**: リクエスト数は無料枠内（月8,640リクエスト程度）
- **合計**: ほぼ無料で運用可能

## 関連ドキュメント

- [Cloud Scheduler ドキュメント](https://cloud.google.com/scheduler/docs)
- [Cloud Run ドキュメント](https://cloud.google.com/run/docs)

