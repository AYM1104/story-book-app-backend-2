#!/bin/bash

# Cloud Runの環境変数GCS_BUCKET_NAMEを確認するスクリプト

# サービス名とリージョンを設定（必要に応じて変更）
SERVICE_NAME="ehonnotane-backend"
REGION="us-west1"

echo "🔍 Cloud Runサービスの環境変数を確認中..."
echo "サービス名: $SERVICE_NAME"
echo "リージョン: $REGION"
echo ""

# 方法1: 環境変数の一覧を表示
echo "=== 方法1: 環境変数の一覧 ==="
gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(spec.template.spec.containers[0].env)' | grep -o 'GCS_BUCKET_NAME=[^,]*' || echo "GCS_BUCKET_NAMEが見つかりません"

echo ""
echo "=== 方法2: YAML形式で詳細確認 ==="
gcloud run services describe $SERVICE_NAME --region=$REGION --format=yaml | grep -A 5 "GCS_BUCKET_NAME" || echo "GCS_BUCKET_NAMEが見つかりません"

echo ""
echo "=== 方法3: Secret Managerから確認 ==="
if gcloud secrets describe GCS_BUCKET_NAME >/dev/null 2>&1; then
    echo "Secret ManagerにGCS_BUCKET_NAMEが存在します"
    echo "値の確認（権限が必要）:"
    gcloud secrets versions access latest --secret="GCS_BUCKET_NAME" 2>/dev/null || echo "権限が不足しているか、シークレットが存在しません"
else
    echo "Secret ManagerにGCS_BUCKET_NAMEが存在しません"
fi

echo ""
echo "=== 方法4: ログから確認 ==="
echo "最新のログからGCS_BUCKET_NAMEを検索:"
gcloud run services logs read $SERVICE_NAME --region=$REGION --limit=100 | grep -i "GCS_BUCKET_NAME\|バケット名" | head -5 || echo "ログにGCS_BUCKET_NAMEが見つかりません"

