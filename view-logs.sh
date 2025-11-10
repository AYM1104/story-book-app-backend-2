#!/bin/bash

# Story Book Backend - Cloud Run ログ表示スクリプト

# 色付きの出力用
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 設定
REGION="us-west1"
SERVICE_NAME="ehonnotane-backend"

echo -e "${GREEN}📋 Cloud Run ログ表示${NC}"
echo "  サービス名: $SERVICE_NAME"
echo "  リージョン: $REGION"
echo ""
echo -e "${YELLOW}💡 ログを停止するには Ctrl+C を押してください${NC}"
echo ""

# リアルタイムログを表示（beta版を使用）
gcloud beta run services logs tail $SERVICE_NAME --region=$REGION --format="table(timestamp,severity,textPayload)"

