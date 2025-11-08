# バックエンドURL

## 本番環境

**バックエンドURL**: https://ehonnotane-backend-20459204449.us-west1.run.app

### エンドポイント

- **ルート**: `GET /` - サービス状態確認
- **ヘルスチェック**: `GET /health` - ヘルスチェック
- **環境変数確認**: `GET /env-check` - 環境変数の確認

### リージョン情報

- **リージョン**: `us-west1`
- **サービス名**: `ehonnotane-backend`

### 確認方法

```bash
# サービス状態の確認
curl https://ehonnotane-backend-20459204449.us-west1.run.app

# ヘルスチェック
curl https://ehonnotane-backend-20459204449.us-west1.run.app/health

# 環境変数の確認
curl https://ehonnotane-backend-20459204449.us-west1.run.app/env-check
```

### ログの確認

```bash
gcloud run services logs read ehonnotane-backend --region=us-west1 --limit=50
```

### サービスの詳細確認

```bash
gcloud run services describe ehonnotane-backend --region=us-west1
```

