#!/bin/bash

# Cloud Runサービスに直接環境変数を設定するスクリプト
# 使用方法: ./set-cloudrun-env.sh

echo "Cloud Runサービスに環境変数を設定します"
echo "================================================"
echo ""

# プロジェクトIDを確認
PROJECT_ID=$(gcloud config get-value project)
echo "プロジェクトID: $PROJECT_ID"
echo ""

echo "環境変数を入力してください:"
echo ""
echo "【必須】以下の環境変数は必ず設定してください"
echo ""

# Supabase関連の環境変数（必須 - データベース用）
read -p "SUPABASE_URL: " SUPABASE_URL
read -p "SUPABASE_ANON_KEY: " SUPABASE_ANON_KEY
read -p "SUPABASE_DB_URL: " SUPABASE_DB_URL

echo ""

# Gemini API関連（必須）
read -p "GEMINI_API_KEY: " GEMINI_API_KEY

echo ""

# Google Cloud Storage（必須 - 画像ストレージ用）
read -p "GCS_BUCKET_NAME (Google Cloud Storageバケット名): " GCS_BUCKET_NAME

echo ""
echo "【推奨】以下の環境変数は推奨されます（Enterでスキップ可）"
echo ""

# Supabase Service Role Key（推奨）
read -p "SUPABASE_SERVICE_ROLE_KEY (データベース管理用): " SUPABASE_SERVICE_ROLE_KEY

echo ""
echo "Cloud Runサービスに環境変数を設定しています..."
echo ""

# 環境変数を構築（STORAGE_TYPE=gcsを明示的に設定）
ENV_VARS="SUPABASE_URL=$SUPABASE_URL,SUPABASE_ANON_KEY=$SUPABASE_ANON_KEY,SUPABASE_DB_URL=$SUPABASE_DB_URL,GEMINI_API_KEY=$GEMINI_API_KEY,GCS_BUCKET_NAME=$GCS_BUCKET_NAME,STORAGE_TYPE=gcs"

# SUPABASE_SERVICE_ROLE_KEYが設定されている場合は追加
if [ -n "$SUPABASE_SERVICE_ROLE_KEY" ]; then
  ENV_VARS="$ENV_VARS,SUPABASE_SERVICE_ROLE_KEY=$SUPABASE_SERVICE_ROLE_KEY"
fi

# Cloud Runサービスを更新
gcloud run services update story-book-backend \
  --region=asia-northeast1 \
  --set-env-vars="$ENV_VARS"

if [ $? -eq 0 ]; then
  echo ""
  echo "================================================"
  echo "✅ 環境変数の設定が完了しました！"
  echo ""
  echo "Cloud Runサービスが自動的に再起動され、新しい環境変数が適用されます。"
  echo ""
  echo "ログを確認:"
  echo "  gcloud run services logs read story-book-backend --region=asia-northeast1 --limit=50"
  echo ""
  echo "サービスのURLを確認:"
  echo "  gcloud run services describe story-book-backend --region=asia-northeast1 --format='value(status.url)'"
  echo ""
else
  echo ""
  echo "❌ エラーが発生しました。"
  echo ""
  echo "サービスが存在しない場合は、先にデプロイを実行してください:"
  echo "  gcloud builds submit --config cloudbuild.yaml ."
fi

