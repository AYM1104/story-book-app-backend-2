#!/bin/bash

# Cloud RunとCloud Buildのサービスアカウントに必要な権限を付与するスクリプト
# 使用方法: ./setup-permissions.sh

echo "================================================"
echo "Cloud Run/Cloud Build 権限設定スクリプト"
echo "================================================"
echo ""

# プロジェクトIDを確認
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
    echo "❌ エラー: プロジェクトIDが設定されていません"
    echo "gcloud config set project YOUR_PROJECT_ID を実行してください"
    exit 1
fi

echo "プロジェクトID: $PROJECT_ID"
echo ""

# プロジェクト番号を取得
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)' 2>/dev/null)
if [ -z "$PROJECT_NUMBER" ]; then
    echo "❌ エラー: プロジェクト番号の取得に失敗しました"
    exit 1
fi

echo "プロジェクト番号: $PROJECT_NUMBER"
echo ""

# サービスアカウントの定義
CLOUD_BUILD_SA="$PROJECT_NUMBER@cloudbuild.gserviceaccount.com"
CLOUD_RUN_SA="$PROJECT_NUMBER-compute@developer.gserviceaccount.com"

echo "設定するサービスアカウント:"
echo "  - Cloud Build: $CLOUD_BUILD_SA"
echo "  - Cloud Run: $CLOUD_RUN_SA"
echo ""

# 必要な権限のリスト
ROLES=(
    "roles/secretmanager.secretAccessor"
    "roles/run.admin"
    "roles/iam.serviceAccountUser"
)

echo "付与する権限:"
for role in "${ROLES[@]}"; do
    echo "  - $role"
done
echo ""

read -p "続行しますか？ (y/N): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "キャンセルしました"
    exit 0
fi

echo ""
echo "権限を付与中..."
echo ""

# Cloud Buildサービスアカウントに権限を付与
echo "1. Cloud Buildサービスアカウントに権限を付与中..."
for role in "${ROLES[@]}"; do
    echo "   → $role を付与中..."
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$CLOUD_BUILD_SA" \
        --role="$role" \
        --condition=None >/dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        echo "   ✅ $role を付与しました"
    else
        echo "   ⚠️ $role の付与に失敗しました（既に付与されている可能性があります）"
    fi
done

echo ""

# Cloud Runサービスアカウントに権限を付与
echo "2. Cloud Runサービスアカウントに権限を付与中..."
for role in "${ROLES[@]}"; do
    echo "   → $role を付与中..."
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$CLOUD_RUN_SA" \
        --role="$role" \
        --condition=None >/dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        echo "   ✅ $role を付与しました"
    else
        echo "   ⚠️ $role の付与に失敗しました（既に付与されている可能性があります）"
    fi
done

echo ""
echo "================================================"
echo "✅ 権限設定が完了しました！"
echo "================================================"
echo ""
echo "現在の権限設定を確認するには:"
echo "  gcloud projects get-iam-policy $PROJECT_ID"
echo ""
echo "Cloud Consoleで確認するには:"
echo "  https://console.cloud.google.com/iam-admin/iam?project=$PROJECT_ID"
echo ""

