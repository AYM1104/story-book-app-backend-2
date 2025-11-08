#!/bin/bash

# カスタムサービスアカウントを作成して、わかりやすい名前を付けるスクリプト
# 使用方法: ./create-custom-service-account.sh <サービスアカウント名>
# 例: ./create-custom-service-account.sh storybook-backend-sa

set -e

# 色付きの出力用
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 引数の確認
if [ $# -lt 1 ]; then
    echo -e "${RED}❌ エラー: サービスアカウント名を指定してください${NC}"
    echo ""
    echo "使用方法:"
    echo "  ./create-custom-service-account.sh <サービスアカウント名>"
    echo ""
    echo "例:"
    echo "  ./create-custom-service-account.sh storybook-backend-sa"
    echo ""
    echo "注意: サービスアカウント名は小文字、ハイフン区切りで指定してください"
    exit 1
fi

SA_NAME=$1
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)

if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ エラー: プロジェクトIDが設定されていません${NC}"
    echo "gcloud config set project YOUR_PROJECT_ID を実行してください"
    exit 1
fi

SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
SA_DISPLAY_NAME="Storybook Backend Service Account"
SA_DESCRIPTION="Storybook Backend用のカスタムサービスアカウント"

echo -e "${GREEN}🔐 カスタムサービスアカウントを作成します${NC}"
echo ""
echo "設定内容:"
echo "  サービスアカウント名: $SA_NAME"
echo "  メールアドレス: $SA_EMAIL"
echo "  表示名: $SA_DISPLAY_NAME"
echo "  説明: $SA_DESCRIPTION"
echo "  プロジェクト: $PROJECT_ID"
echo ""

read -p "続行しますか？ (y/N): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "キャンセルしました"
    exit 0
fi

echo ""
echo "サービスアカウントを作成中..."

# サービスアカウントが既に存在するか確認
if gcloud iam service-accounts describe "$SA_EMAIL" >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️ サービスアカウント $SA_EMAIL は既に存在します${NC}"
    read -p "既存のサービスアカウントを使用しますか？ (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "キャンセルしました"
        exit 0
    fi
else
    # サービスアカウントを作成
    gcloud iam service-accounts create "$SA_NAME" \
        --display-name="$SA_DISPLAY_NAME" \
        --description="$SA_DESCRIPTION" \
        --project="$PROJECT_ID"
    
    echo -e "${GREEN}✅ サービスアカウントを作成しました${NC}"
fi

echo ""
echo "必要な権限を付与中..."

# 必要な権限のリスト
ROLES=(
    "roles/secretmanager.secretAccessor"
    "roles/run.invoker"
    "roles/storage.objectAdmin"
)

for role in "${ROLES[@]}"; do
    echo "  → $role を付与中..."
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:$SA_EMAIL" \
        --role="$role" \
        --condition=None >/dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        echo -e "  ${GREEN}✅ $role を付与しました${NC}"
    else
        echo -e "  ${YELLOW}⚠️ $role の付与に失敗しました（既に付与されている可能性があります）${NC}"
    fi
done

echo ""
echo -e "${GREEN}================================================"
echo "✅ カスタムサービスアカウントの設定が完了しました！"
echo "================================================${NC}"
echo ""
echo "サービスアカウント情報:"
echo "  メールアドレス: $SA_EMAIL"
echo "  表示名: $SA_DISPLAY_NAME"
echo ""
echo "次のステップ:"
echo "1. cloudbuild.yamlでこのサービスアカウントを使用するように設定:"
echo "   --service-account=$SA_EMAIL"
echo ""
echo "2. Cloud Runでこのサービスアカウントを使用するように設定:"
echo "   gcloud run services update ehonnotane-backend \\"
echo "     --service-account=$SA_EMAIL \\"
echo "     --region=us-west1"
echo ""
echo "Cloud Consoleで確認するには:"
echo "  https://console.cloud.google.com/iam-admin/serviceaccounts?project=$PROJECT_ID"
echo ""

