# 環境変数ガイド

このドキュメントでは、Story Book Appバックエンドで使用する環境変数について説明します。

## 環境変数一覧

### 【必須】絶対に設定が必要

#### 1. SUPABASE_URL
- **説明**: SupabaseプロジェクトのURL
- **形式**: `https://xxxxxxxxxxxx.supabase.co`
- **取得方法**: 
  1. Supabaseダッシュボードにログイン
  2. プロジェクトを選択
  3. 「Settings」→「API」
  4. 「Project URL」をコピー

#### 2. SUPABASE_ANON_KEY
- **説明**: Supabase匿名キー（公開可能）
- **形式**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`（長い文字列）
- **取得方法**:
  1. Supabaseダッシュボードにログイン
  2. プロジェクトを選択
  3. 「Settings」→「API」
  4. 「Project API keys」の「anon public」をコピー

#### 3. SUPABASE_DB_URL
- **説明**: PostgreSQLデータベース接続URL
- **形式**: `postgresql://postgres:[YOUR-PASSWORD]@db.xxxxxxxxxxxx.supabase.co:5432/postgres`
- **取得方法**:
  1. Supabaseダッシュボードにログイン
  2. プロジェクトを選択
  3. 「Settings」→「Database」
  4. 「Connection string」の「URI」をコピー
  5. `[YOUR-PASSWORD]`を実際のパスワードに置き換え

#### 4. GEMINI_API_KEY
- **説明**: Google Gemini APIキー（AIでストーリーと画像を生成）
- **形式**: `AIzaSy...`
- **取得方法**:
  1. Google AI Studio (https://aistudio.google.com/app/apikey) にアクセス
  2. 「Create API key」をクリック
  3. 生成されたAPIキーをコピー

#### 5. GCS_BUCKET_NAME
- **説明**: Google Cloud Storageのバケット名（画像ストレージ用）
- **形式**: `your-bucket-name`
- **用途**: AIで生成した画像やアップロードした画像を保存
- **取得方法**:
  1. Google Cloud Console (https://console.cloud.google.com/) にアクセス
  2. 「Cloud Storage」→「バケット」
  3. 既存のバケット名を確認、または新しいバケットを作成
  4. バケット名をコピー
- **⚠️ 注意**: Cloud Runサービスアカウントに、バケットへの読み書き権限を付与する必要があります

---

### 【推奨】機能を完全に使うために必要

#### 6. SUPABASE_SERVICE_ROLE_KEY
- **説明**: Supabaseサービスロールキー（管理者権限、秘密に保持）
- **形式**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`（長い文字列）
- **用途**: データベースの管理操作に必要
- **取得方法**:
  1. Supabaseダッシュボードにログイン
  2. プロジェクトを選択
  3. 「Settings」→「API」
  4. 「Project API keys」の「service_role secret」をコピー
- **⚠️ 注意**: このキーは管理者権限を持つため、絶対に公開しないでください

---

## 不要な環境変数

以下の環境変数は、現在の構成では**設定不要**です：

- ❌ **SUPABASE_STORAGE_BUCKET** - Supabaseストレージは使用しません（GCSを使用）
- ❌ **SUPABASE_JWT_SECRET** - 現在のコードでは使用されていません
- ❌ **GOOGLE_API_KEY** - GEMINI_API_KEYがあれば不要

---

## システム構成

このアプリケーションは以下の構成で動作します：

- **データベース**: Supabase (PostgreSQL)
- **画像ストレージ**: Google Cloud Storage (GCS)
- **AI生成**: Google Gemini API

---

## 環境変数の設定方法

### ローカル開発

`.env`ファイルを作成して設定：

```bash
# .envファイルを作成
cp SUPABASE_ENV_EXAMPLE.txt .env

# .envファイルを編集
# 実際の値を設定してください
```

### Cloud Runデプロイ

#### 事前準備: GCSバケットへの権限設定

Cloud Runサービスアカウントに、GCSバケットへのアクセス権限を付与する必要があります：

```bash
# プロジェクトIDとプロジェクト番号を取得
PROJECT_ID=$(gcloud config get-value project)
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')

# Cloud Runサービスアカウントに「Storage Object Admin」ロールを付与
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member=serviceAccount:$PROJECT_NUMBER-compute@developer.gserviceaccount.com \
  --role=roles/storage.objectAdmin

# または、特定のバケットにのみ権限を付与する場合
gsutil iam ch serviceAccount:$PROJECT_NUMBER-compute@developer.gserviceaccount.com:roles/storage.objectAdmin gs://YOUR_BUCKET_NAME
```

#### 環境変数の設定

スクリプトを使って簡単に設定：

```bash
# 対話形式で環境変数を設定
./set-cloudrun-env.sh
```

または、手動で設定：

```bash
gcloud run services update story-book-backend \
  --region=asia-northeast1 \
  --set-env-vars="SUPABASE_URL=https://xxx.supabase.co,SUPABASE_ANON_KEY=eyJ...,SUPABASE_DB_URL=postgresql://...,GEMINI_API_KEY=AIza...,GCS_BUCKET_NAME=your-bucket-name,STORAGE_TYPE=gcs,SUPABASE_SERVICE_ROLE_KEY=eyJ..."
```

---

## トラブルシューティング

### Q: 環境変数が設定されていないエラーが出る

```
Supabase設定エラー: 以下の環境変数が設定されていません: SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_DB_URL
```

**解決方法:**

1. 環境変数が正しく設定されているか確認:
   ```bash
   # Cloud Runの場合
   gcloud run services describe story-book-backend --region=asia-northeast1
   
   # ローカルの場合
   cat .env
   ```

2. 環境変数を再設定:
   ```bash
   ./set-cloudrun-env.sh
   ```

### Q: 画像のアップロードができない

**原因**: `SUPABASE_SERVICE_ROLE_KEY`が設定されていない可能性があります。

**解決方法**: 
```bash
./set-cloudrun-env.sh
```
を実行して、`SUPABASE_SERVICE_ROLE_KEY`を設定してください。

### Q: AIの生成が動かない

**原因**: `GEMINI_API_KEY`が設定されていないか、APIキーが無効です。

**解決方法**:
1. Google AI Studioで新しいAPIキーを生成
2. 環境変数を再設定

---

## セキュリティのベストプラクティス

1. **`.env`ファイルをGitにコミットしない**
   - `.gitignore`に`.env`が含まれていることを確認

2. **SUPABASE_SERVICE_ROLE_KEYは秘密に保つ**
   - このキーは管理者権限を持ちます
   - 公開リポジトリには絶対にコミットしない

3. **定期的にAPIキーをローテーション**
   - 漏洩の可能性がある場合はすぐにキーを再生成

4. **Cloud Runの環境変数は暗号化される**
   - Cloud Runは環境変数を安全に保存します
   - より高度なセキュリティが必要な場合はSecret Managerの使用を検討

