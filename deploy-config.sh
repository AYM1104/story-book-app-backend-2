# デプロイ設定ファイル
# このファイルでサービス名やイメージ名を一元管理します

# Cloud Runサービス名（小文字、ハイフン区切り推奨）
SERVICE_NAME="storybook-backend-api"

# Dockerイメージ名（小文字、ハイフン区切り推奨）
IMAGE_NAME="storybook-backend"

# リージョン
REGION="us-west1"

# ポート番号
PORT="8080"

# リソース設定
MEMORY="2Gi"
CPU="2"
MAX_INSTANCES="10"

