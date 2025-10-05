#!/bin/bash

# Story Book Backend - Cloud Run デプロイスクリプト

set -e  # エラー時にスクリプトを停止

# 色付きの出力用
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 設定
PROJECT_ID=""
REGION="asia-northeast1"
SERVICE_NAME="story-book-backend"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo -e "${GREEN}🚀 Story Book Backend - Cloud Run デプロイスクリプト${NC}"
echo ""

# プロジェクトIDの確認
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ エラー: PROJECT_IDが設定されていません${NC}"
    echo "スクリプト内のPROJECT_ID変数を設定してください"
    exit 1
fi

echo -e "${YELLOW}📋 デプロイ設定:${NC}"
echo "  プロジェクトID: $PROJECT_ID"
echo "  リージョン: $REGION"
echo "  サービス名: $SERVICE_NAME"
echo "  イメージ名: $IMAGE_NAME"
echo ""

# 確認
read -p "デプロイを続行しますか？ (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}デプロイをキャンセルしました${NC}"
    exit 1
fi

echo -e "${GREEN}🔧 必要なAPIの有効化...${NC}"
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

echo -e "${GREEN}🔨 Dockerイメージのビルド...${NC}"
docker build -t $IMAGE_NAME .

echo -e "${GREEN}📤 イメージをGoogle Container Registryにプッシュ...${NC}"
docker push $IMAGE_NAME

echo -e "${GREEN}🚀 Cloud Runにデプロイ...${NC}"
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_NAME \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --memory 2Gi \
  --cpu 2 \
  --max-instances 10 \
  --min-instances 0 \
  --timeout 300

echo -e "${GREEN}✅ デプロイが完了しました！${NC}"
echo ""

# サービスのURLを取得
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")
echo -e "${GREEN}🌐 サービスURL: $SERVICE_URL${NC}"
echo ""

# ヘルスチェック
echo -e "${YELLOW}🔍 ヘルスチェックを実行中...${NC}"
if curl -s -f "$SERVICE_URL" > /dev/null; then
    echo -e "${GREEN}✅ サービスが正常に動作しています${NC}"
else
    echo -e "${RED}❌ サービスへの接続に失敗しました${NC}"
    echo "ログを確認してください:"
    echo "gcloud run services logs read $SERVICE_NAME --region=$REGION"
fi

echo ""
echo -e "${GREEN}🎉 デプロイが完了しました！${NC}"
echo -e "${YELLOW}💡 次のステップ:${NC}"
echo "  1. 環境変数の設定: gcloud run services update $SERVICE_NAME --region=$REGION --set-env-vars=\"KEY=VALUE\""
echo "  2. ログの確認: gcloud run services logs read $SERVICE_NAME --region=$REGION"
echo "  3. サービス詳細: gcloud run services describe $SERVICE_NAME --region=$REGION"
