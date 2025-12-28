# GCSバケット名の修正方法

## 問題
現在のバケット名: `ehonnotane-images-strage`
エラー: `The specified bucket does not exist.`

## 解決方法

### 1. 正しいバケット名を確認

Google Cloud Consoleで確認:
1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. ストレージ > バケット に移動
3. プロジェクト内のバケット一覧を確認
4. `ehonnotane` や `image` を含むバケット名を探す

### 2. .envファイルを修正

`backend/backend/.env` ファイル（または `backend/.env`）を開いて、以下を修正:

```bash
# 間違い（現在）
GCS_BUCKET_NAME=ehonnotane-images-strage

# 正しい（例 - 実際のバケット名に置き換えてください）
GCS_BUCKET_NAME=ehonnotane-images-storage
```

### 3. よくあるバケット名のパターン

- `ehonnotane-images-storage` (strage → storage の修正)
- `ehonnotane-images` (strage 部分を削除)
- `ehonnotane-storage`
- `ehonnotane-image-storage`

### 4. バックエンドサーバーを再起動

```bash
# バックエンドサーバーを再起動
cd backend/backend
./venv/bin/uvicorn app.main:app --reload
```

### 5. 再度テストを実行

```bash
cd backend
python test_storybook_generation.py /Users/ayu/Downloads/astro.png
```

## バケットが存在しない場合

もしバケットが存在しない場合は、新しく作成する必要があります:

```bash
# gcloud CLIを使用（インストール済みの場合）
gsutil mb -p ayu1104 -c STANDARD -l asia-northeast1 gs://ehonnotane-images-storage
```

または、Google Cloud Consoleから:
1. ストレージ > バケット > バケットを作成
2. バケット名を入力（例: `ehonnotane-images-storage`）
3. ロケーション: `asia-northeast1` (東京)
4. ストレージクラス: `Standard`

