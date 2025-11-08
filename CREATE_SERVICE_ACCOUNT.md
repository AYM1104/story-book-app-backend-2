# カスタムサービスアカウント作成手順（Cloud Console）

## 手順

### 1. Cloud Consoleでサービスアカウントを作成

1. [サービスアカウントのページ](https://console.cloud.google.com/iam-admin/serviceaccounts?project=ayu1104)にアクセス
2. 「サービスアカウントを作成」をクリック
3. 以下の情報を入力：
   - **サービスアカウント名**: `ehonnotane-backend-sa`
   - **サービスアカウントID**: `ehonnotane-backend-sa`（自動入力）
   - **説明**: `Storybook Backend用のカスタムサービスアカウント`
4. 「作成して続行」をクリック

### 2. 必要な権限を付与

「ロールを選択」で以下の権限を追加：
- `Secret Manager Secret Accessor` (roles/secretmanager.secretAccessor)
- `Cloud Run Invoker` (roles/run.invoker)
- `Storage Object Admin` (roles/storage.objectAdmin)

「続行」→「完了」をクリック

### 3. 確認

作成されたサービスアカウントのメールアドレス：
```
ehonnotane-backend-sa@ayu1104.iam.gserviceaccount.com
```

## コマンドラインで作成する場合

gcloudコマンドが利用可能な場合：

```bash
cd /Users/ayu/create/native_app/storybook_backend/story-book-app-backend-2
chmod +x create-custom-service-account.sh
./create-custom-service-account.sh ehonnotane-backend-sa
```

## 次のステップ

サービスアカウントを作成したら、変更をコミットしてプッシュ：

```bash
git add cloudbuild.yaml
git commit -m "Use custom service account: ehonnotane-backend-sa"
git push origin main
```

次回のデプロイで、新しいカスタムサービスアカウントが使用されます。

