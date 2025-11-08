# カスタムサービスアカウントの設定方法

## 概要

デフォルトのサービスアカウント（`*-compute@developer.gserviceaccount.com`）の代わりに、わかりやすい名前のカスタムサービスアカウントを作成して使用できます。

## 手順

### 1. カスタムサービスアカウントを作成

```bash
# スクリプトに実行権限を付与
chmod +x create-custom-service-account.sh

# カスタムサービスアカウントを作成（わかりやすい名前を指定）
./create-custom-service-account.sh storybook-backend-sa
```

### 2. cloudbuild.yamlでサービスアカウントを指定

`cloudbuild.yaml`のCloud Runデプロイステップに`--service-account`オプションを追加：

```yaml
- name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
  entrypoint: 'gcloud'
  args:
    - 'run'
    - 'deploy'
    - 'ehonnotane-backend'
    - '--image'
    - 'gcr.io/$PROJECT_ID/story-book-backend:$BUILD_ID'
    - '--region'
    - 'us-west1'
    - '--platform'
    - 'managed'
    - '--allow-unauthenticated'
    - '--service-account'  # この行を追加
    - 'storybook-backend-sa@$PROJECT_ID.iam.gserviceaccount.com'  # この行を追加
    - '--port'
    - '8080'
    # ... その他のオプション
```

### 3. Cloud Consoleで確認

作成したサービスアカウントは、以下のURLで確認できます：

```
https://console.cloud.google.com/iam-admin/serviceaccounts?project=YOUR_PROJECT_ID
```

## メリット

1. **わかりやすい名前**: `storybook-backend-sa@project.iam.gserviceaccount.com`のように、用途が明確
2. **管理しやすい**: プロジェクトごとに専用のサービスアカウントを作成できる
3. **権限の分離**: 各サービスアカウントに必要な最小限の権限のみを付与できる

## 注意事項

- サービスアカウント名は小文字、ハイフン区切りで指定してください
- サービスアカウント名は変更できません（削除して再作成する必要があります）
- 既存のサービスで使用中のサービスアカウントは削除できません

