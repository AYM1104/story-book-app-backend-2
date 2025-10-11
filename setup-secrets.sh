#!/bin/bash

# Google Cloud Secret Managerにシークレットを設定するスクリプト
# 使用方法: ./setup-secrets.sh

echo "Google Cloud Secret Managerにシークレットを設定します"
echo "================================================"
echo ""

# プロジェクトIDを確認
PROJECT_ID=$(gcloud config get-value project)
echo "プロジェクトID: $PROJECT_ID"
echo ""

# Secret Manager APIを有効化
echo "Secret Manager APIを有効化しています..."
gcloud services enable secretmanager.googleapis.com

echo ""
echo "環境変数を入力してください:"
echo ""

# Supabase関連の環境変数
read -p "SUPABASE_URL: " SUPABASE_URL
read -p "SUPABASE_ANON_KEY: " SUPABASE_ANON_KEY
read -p "SUPABASE_SERVICE_ROLE_KEY: " SUPABASE_SERVICE_ROLE_KEY
read -p "SUPABASE_DB_URL: " SUPABASE_DB_URL
read -p "SUPABASE_STORAGE_BUCKET (デフォルト: storybook-images): " SUPABASE_STORAGE_BUCKET
SUPABASE_STORAGE_BUCKET=${SUPABASE_STORAGE_BUCKET:-storybook-images}
read -p "SUPABASE_JWT_SECRET: " SUPABASE_JWT_SECRET

echo ""

# Gemini API関連
read -p "GEMINI_API_KEY: " GEMINI_API_KEY
read -p "GOOGLE_API_KEY: " GOOGLE_API_KEY

echo ""

# GCS関連
read -p "GCS_BUCKET_NAME: " GCS_BUCKET_NAME

echo ""
echo "シークレットを作成・更新しています..."
echo ""

# シークレットを作成・更新する関数
create_or_update_secret() {
  local secret_name=$1
  local secret_value=$2
  
  # シークレットが存在するか確認
  if gcloud secrets describe "$secret_name" >/dev/null 2>&1; then
    # 存在する場合は新しいバージョンを追加
    echo "$secret_value" | gcloud secrets versions add "$secret_name" --data-file=-
    echo "✓ $secret_name を更新しました"
  else
    # 存在しない場合は新規作成
    echo "$secret_value" | gcloud secrets create "$secret_name" --data-file=-
    echo "✓ $secret_name を作成しました"
  fi
}

# 各シークレットを作成・更新
create_or_update_secret "SUPABASE_URL" "$SUPABASE_URL"
create_or_update_secret "SUPABASE_ANON_KEY" "$SUPABASE_ANON_KEY"
create_or_update_secret "SUPABASE_SERVICE_ROLE_KEY" "$SUPABASE_SERVICE_ROLE_KEY"
create_or_update_secret "SUPABASE_DB_URL" "$SUPABASE_DB_URL"
create_or_update_secret "SUPABASE_STORAGE_BUCKET" "$SUPABASE_STORAGE_BUCKET"
create_or_update_secret "SUPABASE_JWT_SECRET" "$SUPABASE_JWT_SECRET"
create_or_update_secret "GEMINI_API_KEY" "$GEMINI_API_KEY"
create_or_update_secret "GOOGLE_API_KEY" "$GOOGLE_API_KEY"
create_or_update_secret "GCS_BUCKET_NAME" "$GCS_BUCKET_NAME"

echo ""
echo "================================================"
echo "✅ すべてのシークレットが設定されました！"
echo ""
echo "次のステップ:"
echo "1. Cloud Build サービスアカウントに Secret Manager へのアクセス権限を付与:"
echo "   PROJECT_NUMBER=\$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')"
echo "   gcloud projects add-iam-policy-binding $PROJECT_ID \\"
echo "     --member=serviceAccount:\$PROJECT_NUMBER@cloudbuild.gserviceaccount.com \\"
echo "     --role=roles/secretmanager.secretAccessor"
echo ""
echo "2. Cloud Run サービスアカウントにも権限を付与:"
echo "   gcloud projects add-iam-policy-binding $PROJECT_ID \\"
echo "     --member=serviceAccount:\$PROJECT_NUMBER-compute@developer.gserviceaccount.com \\"
echo "     --role=roles/secretmanager.secretAccessor"
echo ""
echo "3. デプロイを実行:"
echo "   gcloud builds submit --config cloudbuild.yaml ."
echo ""

