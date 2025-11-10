#!/bin/bash

# Story Book Backend - Cloud Run デプロイスクリプト

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

# 必須シークレットのリスト
REQUIRED_SECRETS=(
  "SUPABASE_URL"
  "SUPABASE_ANON_KEY"
  "SUPABASE_DB_URL"
  "GCS_BUCKET_NAME"
)

echo -e "${GREEN}🚀 Story Book Backend - Cloud Run デプロイスクリプト${NC}"
echo ""

# プロジェクトIDの確認
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ エラー: プロジェクトIDが設定されていません${NC}"
    echo "以下のコマンドでプロジェクトを設定してください:"
    echo "  gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo -e "${YELLOW}📋 デプロイ設定:${NC}"
echo "  プロジェクトID: $PROJECT_ID"
echo "  リージョン: $REGION"
echo "  サービス名: $SERVICE_NAME"
echo ""

# Secret Managerの設定確認
echo -e "${BLUE}🔍 Secret Managerの設定を確認中...${NC}"
MISSING_SECRETS=()
for secret in "${REQUIRED_SECRETS[@]}"; do
    if ! gcloud secrets describe "$secret" >/dev/null 2>&1; then
        MISSING_SECRETS+=("$secret")
    fi
done

if [ ${#MISSING_SECRETS[@]} -gt 0 ]; then
    echo -e "${RED}❌ 以下のシークレットがSecret Managerに設定されていません:${NC}"
    for secret in "${MISSING_SECRETS[@]}"; do
        echo "  - $secret"
    done
    echo ""
    echo -e "${YELLOW}💡 シークレットを設定するには、以下のコマンドを実行してください:${NC}"
    echo "  ./setup-secrets.sh"
    echo ""
    read -p "続行しますか？（シークレットが後で設定される場合） (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}デプロイをキャンセルしました${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ すべての必須シークレットが設定されています${NC}"
fi

echo ""

# 確認
read -p "デプロイを続行しますか？ (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}デプロイをキャンセルしました${NC}"
    exit 1
fi

echo -e "${GREEN}🔧 必要なAPIの有効化...${NC}"
gcloud services enable cloudbuild.googleapis.com --quiet
gcloud services enable run.googleapis.com --quiet
gcloud services enable containerregistry.googleapis.com --quiet
gcloud services enable secretmanager.googleapis.com --quiet
gcloud services enable cloudresourcemanager.googleapis.com --quiet

echo ""
echo -e "${GREEN}🔨 Cloud Buildでビルドとデプロイを実行中...${NC}"
echo -e "${YELLOW}（これには数分かかる場合があります）${NC}"
echo ""

# Cloud Buildを使用してデプロイ
gcloud builds submit --config cloudbuild.yaml .

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ デプロイが完了しました！${NC}"
    echo ""
    
    # サービスのURLを取得
    SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)" 2>/dev/null)
    if [ -n "$SERVICE_URL" ]; then
        echo -e "${GREEN}🌐 サービスURL: $SERVICE_URL${NC}"
        echo ""
        
        # ヘルスチェック
        echo -e "${YELLOW}🔍 ヘルスチェックを実行中...${NC}"
        sleep 5  # サービスが起動するまで少し待つ
        if curl -s -f "$SERVICE_URL/health" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ サービスが正常に動作しています${NC}"
        else
            echo -e "${YELLOW}⚠️  ヘルスチェックに失敗しました（サービスが起動中かもしれません）${NC}"
        fi
    fi
    
    echo ""
    echo -e "${GREEN}🎉 デプロイが完了しました！${NC}"
    echo ""
    echo -e "${YELLOW}💡 次のステップ:${NC}"
    echo "  1. ログの確認:"
    echo "     gcloud run services logs read $SERVICE_NAME --region=$REGION --limit=50"
    echo ""
    echo "  2. サービスの詳細確認:"
    echo "     gcloud run services describe $SERVICE_NAME --region=$REGION"
    echo ""
    echo "  3. 環境変数の確認:"
    echo "     gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(spec.template.spec.containers[0].env)'"
else
    echo ""
    echo -e "${RED}❌ デプロイに失敗しました${NC}"
    echo "ログを確認してください:"
    echo "  gcloud builds list --limit=1"
    exit 1
fi
