#!/bin/bash

# サービス名とイメージ名を一括変更するスクリプト
# 使用方法: ./rename-service.sh <新しいサービス名> <新しいイメージ名>
# 例: ./rename-service.sh storybook-backend-api storybook-backend

set -e

# 色付きの出力用
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 引数の確認
if [ $# -lt 2 ]; then
    echo -e "${RED}❌ エラー: 引数が不足しています${NC}"
    echo ""
    echo "使用方法:"
    echo "  ./rename-service.sh <新しいサービス名> <新しいイメージ名>"
    echo ""
    echo "例:"
    echo "  ./rename-service.sh storybook-backend-api storybook-backend"
    echo ""
    echo "現在の設定:"
    echo "  サービス名: ehonnotane-backend"
    echo "  イメージ名: story-book-backend"
    exit 1
fi

NEW_SERVICE_NAME=$1
NEW_IMAGE_NAME=$2

# 現在の名前
OLD_SERVICE_NAME="ehonnotane-backend"
OLD_IMAGE_NAME="story-book-backend"

echo -e "${GREEN}🔄 サービス名とイメージ名を変更します${NC}"
echo ""
echo "変更内容:"
echo "  サービス名: ${OLD_SERVICE_NAME} → ${NEW_SERVICE_NAME}"
echo "  イメージ名: ${OLD_IMAGE_NAME} → ${NEW_IMAGE_NAME}"
echo ""

read -p "続行しますか？ (y/N): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "キャンセルしました"
    exit 0
fi

echo ""
echo "ファイルを変更中..."

# 変更するファイルのリスト
FILES=(
    "cloudbuild.yaml"
    "deploy.sh"
    "set-cloudrun-env.sh"
    ".github/workflows/deploy-backend.yml"
)

# 各ファイルを変更
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${BLUE}📝 $file を変更中...${NC}"
        
        # サービス名を変更
        sed -i.bak "s/${OLD_SERVICE_NAME}/${NEW_SERVICE_NAME}/g" "$file"
        
        # イメージ名を変更
        sed -i.bak "s/${OLD_IMAGE_NAME}/${NEW_IMAGE_NAME}/g" "$file"
        
        # バックアップファイルを削除
        rm -f "${file}.bak"
        
        echo -e "${GREEN}  ✅ $file を変更しました${NC}"
    else
        echo -e "${YELLOW}  ⚠️ $file が見つかりません（スキップ）${NC}"
    fi
done

# ドキュメントファイルも変更（オプション）
DOC_FILES=(
    "DEPLOY.md"
    "BACKEND_URL.md"
    "README.md"
)

read -p "ドキュメントファイルも変更しますか？ (y/N): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    for file in "${DOC_FILES[@]}"; do
        if [ -f "$file" ]; then
            echo -e "${BLUE}📝 $file を変更中...${NC}"
            sed -i.bak "s/${OLD_SERVICE_NAME}/${NEW_SERVICE_NAME}/g" "$file"
            sed -i.bak "s/${OLD_IMAGE_NAME}/${NEW_IMAGE_NAME}/g" "$file"
            rm -f "${file}.bak"
            echo -e "${GREEN}  ✅ $file を変更しました${NC}"
        fi
    done
fi

echo ""
echo -e "${GREEN}================================================"
echo "✅ 名前の変更が完了しました！"
echo "================================================${NC}"
echo ""
echo "変更されたファイル:"
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  - $file"
    fi
done
echo ""
echo "次のステップ:"
echo "  1. 変更内容を確認: git diff"
echo "  2. 変更をコミット: git add . && git commit -m 'Rename service and image'"
echo "  3. 既存のCloud Runサービスを削除（必要に応じて）:"
echo "     gcloud run services delete ${OLD_SERVICE_NAME} --region=us-west1"
echo "  4. 新しい名前でデプロイ: git push origin main"
echo ""

