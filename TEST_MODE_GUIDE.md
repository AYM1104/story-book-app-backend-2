# テストモードガイド

アプリを起動しなくても絵本生成の一連の流れをテストできる機能です。

## 概要

テストモードを有効にすると、Auth0の認証をバイパスしてダミーユーザーでAPIをテストできます。これにより、iOSアプリを起動せずにバックエンドの機能を素早くテストできます。

## 設定方法

### 1. 環境変数の設定

`.env`ファイルまたは環境変数に以下を追加してください：

```bash
# テストモードを有効化
ENABLE_TEST_MODE=true

# テスト用のユーザーID（オプション、デフォルト: test|123456789）
TEST_USER_ID=test|123456789

# バックエンドのURL（テストスクリプト用、オプション）
BACKEND_URL=http://localhost:8000
```

### 2. バックエンドサーバーの起動

```bash
cd backend
./venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. テストスクリプトの実行

```bash
cd backend
python test_storybook_generation.py
```

または、画像ファイルを指定して実行：

```bash
python test_storybook_generation.py /path/to/image.jpg
```

## テストフロー

テストスクリプトは以下のフローを自動実行します：

1. **ヘルスチェック**: バックエンドサーバーに接続できるか確認
2. **画像アップロード**: 指定された画像をアップロード
3. **ストーリー設定作成**: 画像からストーリー設定を自動生成
4. **テーマ生成**: 3つのテーマ案を生成
5. **テーマ選択と物語生成**: 選択したテーマで物語を生成
6. **ストーリーブック作成**: ストーリーブックを作成

## 注意事項

⚠️ **重要**: テストモードは本番環境では使用しないでください！

- テストモードは開発・テスト環境でのみ使用してください
- 本番環境では必ず `ENABLE_TEST_MODE=false` または環境変数を設定しないでください
- テストモードが有効な場合、認証がバイパスされるため、セキュリティリスクがあります

## トラブルシューティング

### バックエンドサーバーに接続できない

```
❌ バックエンドサーバーに接続できません
```

**解決方法**:
- バックエンドサーバーが起動しているか確認
- `BACKEND_URL` 環境変数が正しいか確認
- ファイアウォールやネットワーク設定を確認

### 画像アップロードが失敗する

```
❌ 画像アップロード失敗
```

**解決方法**:
- 画像ファイルのパスが正しいか確認
- 画像ファイルが存在するか確認
- ファイルサイズが10MB以下か確認
- サポートされている形式（JPEG, PNG, WebP）か確認

### 認証エラーが発生する

```
❌ 認証トークンが必要です
```

**解決方法**:
- `ENABLE_TEST_MODE=true` が設定されているか確認
- バックエンドサーバーを再起動して環境変数を読み込む
- `.env` ファイルが正しく読み込まれているか確認

## カスタマイズ

### テストユーザーIDの変更

```bash
export TEST_USER_ID=my_test_user|987654321
python test_storybook_generation.py
```

### バックエンドURLの変更

```bash
export BACKEND_URL=http://192.168.1.100:8000
python test_storybook_generation.py
```

## 次のステップ

テストが成功したら、以下のAPIを呼び出して画像生成をテストできます：

```bash
curl -X POST "http://localhost:8000/api/images/generate-storybook-all-pages-image-to-image" \
  -H "Content-Type: application/json" \
  -d '{
    "storybook_id": <storybook_id>,
    "user_id": "test|123456789"
  }'
```

## 関連ファイル

- `backend/app/core/security/auth0_jwt.py`: 認証バイパスロジック
- `backend/test_storybook_generation.py`: テストスクリプト
- `backend/ENV_EXAMPLE.txt`: 環境変数の例

