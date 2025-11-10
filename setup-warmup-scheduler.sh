#!/bin/bash

# Cloud Run ウォームアップ用 Cloud Scheduler 設定スクリプト
# 5分おきに/healthエンドポイントにリクエストを送信して、Cloud Runのコールドスタートを防ぎます

set -e  # エラー時にスクリプトを停止

# 色付きの出力用
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 設定
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
REGION="us-west1"
SERVICE_NAME="ehonnotane-backend"
SCHEDULER_JOB_NAME="warmup-health-check"
SERVICE_ACCOUNT_NAME="cloud-scheduler-invoker"
SCHEDULER_REGION="us-west1"  # Cloud Schedulerのリージョン（Cloud Runと同じリージョン）

echo -e "${GREEN}🔧 Cloud Run ウォームアップ用 Cloud Scheduler 設定スクリプト${NC}"
echo ""

# プロジェクトIDの確認
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ エラー: プロジェクトIDが設定されていません${NC}"
    echo "以下のコマンドでプロジェクトを設定してください:"
    echo "  gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo -e "${YELLOW}📋 設定情報:${NC}"
echo "  プロジェクトID: $PROJECT_ID"
echo "  Cloud Runリージョン: $REGION"
echo "  Cloud Schedulerリージョン: $SCHEDULER_REGION"
echo "  サービス名: $SERVICE_NAME"
echo "  ジョブ名: $SCHEDULER_JOB_NAME"
echo "  サービスアカウント名: $SERVICE_ACCOUNT_NAME"
echo ""

# Cloud RunサービスのURLを取得
echo -e "${BLUE}🔍 Cloud RunサービスのURLを取得中...${NC}"
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)" 2>/dev/null)

if [ -z "$SERVICE_URL" ]; then
    echo -e "${RED}❌ エラー: Cloud Runサービス '$SERVICE_NAME' が見つかりません${NC}"
    echo "サービスが存在するか確認してください:"
    echo "  gcloud run services list --region=$REGION"
    exit 1
fi

echo -e "${GREEN}✅ サービスURL: $SERVICE_URL${NC}"
echo ""

# 必要なAPIの有効化
echo -e "${BLUE}🔧 必要なAPIの有効化...${NC}"
gcloud services enable cloudscheduler.googleapis.com --quiet || true
gcloud services enable run.googleapis.com --quiet || true
echo -e "${GREEN}✅ APIの有効化が完了しました${NC}"
echo ""

# サービスアカウントの作成（存在しない場合）
echo -e "${BLUE}🔍 サービスアカウントの確認...${NC}"
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

if gcloud iam service-accounts describe "$SERVICE_ACCOUNT_EMAIL" >/dev/null 2>&1; then
    echo -e "${GREEN}✅ サービスアカウントは既に存在します: $SERVICE_ACCOUNT_EMAIL${NC}"
else
    echo -e "${YELLOW}📝 サービスアカウントを作成中...${NC}"
    gcloud iam service-accounts create "$SERVICE_ACCOUNT_NAME" \
        --display-name="Cloud Scheduler Invoker for Cloud Run Warmup" \
        --description="Cloud SchedulerからCloud Runサービスを呼び出すためのサービスアカウント" \
        --project="$PROJECT_ID"
    echo -e "${GREEN}✅ サービスアカウントを作成しました: $SERVICE_ACCOUNT_EMAIL${NC}"
fi
echo ""

# Cloud RunサービスへのInvoke権限を付与
echo -e "${BLUE}🔐 Cloud RunサービスへのInvoke権限を付与中...${NC}"
gcloud run services add-iam-policy-binding "$SERVICE_NAME" \
    --region="$REGION" \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/run.invoker" \
    --project="$PROJECT_ID" \
    --quiet

echo -e "${GREEN}✅ Invoke権限を付与しました${NC}"
echo ""

# 既存のジョブを削除（存在する場合）
echo -e "${BLUE}🔍 既存のジョブを確認中...${NC}"
if gcloud scheduler jobs describe "$SCHEDULER_JOB_NAME" --location="$SCHEDULER_REGION" --project="$PROJECT_ID" >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  既存のジョブが見つかりました。削除して再作成します...${NC}"
    gcloud scheduler jobs delete "$SCHEDULER_JOB_NAME" \
        --location="$SCHEDULER_REGION" \
        --project="$PROJECT_ID" \
        --quiet
    echo -e "${GREEN}✅ 既存のジョブを削除しました${NC}"
fi
echo ""

# Cloud Schedulerジョブの作成
echo -e "${BLUE}📅 Cloud Schedulerジョブを作成中...${NC}"
HEALTH_CHECK_URL="${SERVICE_URL}/health"

gcloud scheduler jobs create http "$SCHEDULER_JOB_NAME" \
    --location="$SCHEDULER_REGION" \
    --schedule="*/5 * * * *" \
    --uri="$HEALTH_CHECK_URL" \
    --http-method="GET" \
    --oidc-service-account-email="$SERVICE_ACCOUNT_EMAIL" \
    --oidc-token-audience="$SERVICE_URL" \
    --description="Cloud Runサービスのウォームアップ用ジョブ（5分おきに/healthエンドポイントにアクセス）" \
    --time-zone="Asia/Tokyo" \
    --project="$PROJECT_ID"

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ Cloud Schedulerジョブを作成しました！${NC}"
    echo ""
    echo -e "${YELLOW}📋 ジョブ情報:${NC}"
    echo "  ジョブ名: $SCHEDULER_JOB_NAME"
    echo "  スケジュール: 5分おき（*/5 * * * *）"
    echo "  ターゲットURL: $HEALTH_CHECK_URL"
    echo "  サービスアカウント: $SERVICE_ACCOUNT_EMAIL"
    echo ""
    echo -e "${GREEN}🎉 設定が完了しました！${NC}"
    echo ""
    echo -e "${YELLOW}💡 次のステップ:${NC}"
    echo "  1. ジョブの状態を確認:"
    echo "     gcloud scheduler jobs describe $SCHEDULER_JOB_NAME --location=$SCHEDULER_REGION"
    echo ""
    echo "  2. ジョブを手動で実行してテスト:"
    echo "     gcloud scheduler jobs run $SCHEDULER_JOB_NAME --location=$SCHEDULER_REGION"
    echo ""
    echo "  3. ジョブの実行履歴を確認:"
    echo "     gcloud scheduler jobs describe $SCHEDULER_JOB_NAME --location=$SCHEDULER_REGION --format='value(status)'"
    echo ""
    echo "  4. Cloud Runのログでリクエストを確認:"
    echo "     gcloud run services logs read $SERVICE_NAME --region=$REGION --limit=20"
    echo ""
else
    echo ""
    echo -e "${RED}❌ ジョブの作成に失敗しました${NC}"
    exit 1
fi

