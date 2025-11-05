# Auth0環境変数ガイド

このドキュメントでは、Story Book Appバックエンドで使用するAuth0関連の環境変数について説明します。

## 環境変数一覧

### 【必須】絶対に設定が必要

#### 1. AUTH0_DOMAIN
- **説明**: Auth0テナントのドメイン
- **形式**: `your-domain.auth0.com`
- **現在の値**: `ehonnotane.jp.auth0.com`
- **取得方法**: 
  1. Auth0ダッシュボードにログイン
  2. 「Settings」→「General」
  3. 「Domain」をコピー

#### 2. AUTH0_API_AUDIENCE
- **説明**: Auth0で作成したAPIのIdentifier
- **形式**: `https://api.your-app-name`
- **現在の値**: `https://api.ehonnotane`
- **取得方法**:
  1. Auth0ダッシュボードにログイン
  2. 「Applications」→「APIs」
  3. 作成したAPIの「Identifier」をコピー

#### 3. AUTH0_NATIVE_CLIENT_ID
- **説明**: Native App用のClient ID（SwiftUIアプリ用）
- **形式**: `長いランダム文字列`
- **現在の値**: `b1sTk9gTW2rjddFtvu0w7ZrsFYk2ldfh`
- **取得方法**:
  1. Auth0ダッシュボードにログイン
  2. 「Applications」→「Applications」
  3. Native Appの「Client ID」をコピー

### 【必須】Auth0 Management API用

#### 4. AUTH0_MANAGEMENT_CLIENT_ID
- **説明**: Auth0 Management APIを呼び出すためのMachine to MachineアプリのClient ID
- **形式**: `長いランダム文字列`
- **用途**: バックエンドでユーザー削除（/api/v2/users）などの管理操作を行う際に使用
- **取得方法**:
  1. Auth0ダッシュボードで「Applications」→「Applications」→「Create Application」
  2. **Machine to Machine Applications**を選択
  3. Auth0 Management APIを許可し、`read:users`と`delete:users`スコープを付与
  4. 作成したアプリの「Client ID」をコピー

#### 5. AUTH0_MANAGEMENT_CLIENT_SECRET
- **説明**: Auth0 Management API用Machine to MachineアプリのClient Secret
- **形式**: `長いランダム文字列`
- **用途**: バックエンドから`client_credentials`フローでトークンを取得する際に使用
- **取得方法**:
  1. 上記のMachine to Machineアプリの「Settings」タブを開く
  2. 「Client Secret」をコピー
- **⚠️ 注意**: この値は秘密に保持してください（Git管理下に置かないこと）

### 【任意】互換用（既存のWebアプリ設定）

#### 6. AUTH0_WEB_CLIENT_ID
- **説明**: 既存環境と互換性を保つためのWeb App用Client ID
- **用途**: 現状では直接使用していませんが、将来の機能や後方互換のために保持

#### 7. AUTH0_WEB_CLIENT_SECRET
- **説明**: 既存環境と互換性を保つためのWeb App用Client Secret
- **⚠️ 注意**: Machine to Machineアプリの値とは別物です。混在させないようにしてください。

#### 8. AUTH0_MANAGEMENT_AUDIENCE（任意）
- **説明**: Management API向けのAudienceを上書きする場合に使用
- **デフォルト**: `https://{AUTH0_DOMAIN}/api/v2/`
- **用途**: 特殊なカスタムドメインなどでAudienceを切り替える必要がある場合のみ設定

---

## その他の環境変数

### AI・画像生成用

#### 9. GEMINI_API_KEY
- **説明**: Google Gemini APIキー（AIでストーリーと画像を生成）
- **形式**: `AIzaSy...`
- **取得方法**:
  1. Google AI Studio (https://aistudio.google.com/app/apikey) にアクセス
  2. 「Create API key」をクリック
  3. 生成されたAPIキーをコピー

#### 10. GCS_BUCKET_NAME
- **説明**: Google Cloud Storageのバケット名（画像ストレージ用）
- **形式**: `your-bucket-name`
- **用途**: AIで生成した画像やアップロードした画像を保存

---

## Auth0設定手順

### 1. Auth0ダッシュボードでの設定

#### Step 1: APIの作成
1. Auth0ダッシュボードにログイン
2. 「Applications」→「APIs」→「Create API」
3. 以下の設定でAPIを作成：
   - **Name**: `Story Book API`
   - **Identifier**: `https://api.ehonnotane`
   - **Signing Algorithm**: `RS256`

#### Step 2: Native Appの作成
1. 「Applications」→「Applications」→「Create Application」
2. 以下の設定でNative Appを作成：
   - **Name**: `Story Book iOS App`
   - **Application Type**: `Native`
3. 設定を完了し、Client IDをコピー

#### Step 3: Googleソーシャル接続の設定
1. 「Authentication」→「Social」→「Create Connection」
2. 「Google」を選択
3. Google OAuth 2.0の設定：
   - **Client ID**: Google Cloud Consoleで作成したOAuth 2.0クライアントID
   - **Client Secret**: Google Cloud Consoleで作成したOAuth 2.0クライアントシークレット
4. 「Applications」タブでNative Appを有効化

#### Step 4: Management API用Machine to Machineアプリの作成
1. 「Applications」→「Applications」→「Create Application」
2. **Machine to Machine Applications**を選択し、名称を例: `Story Book Backend`
3. 作成後、「APIs」タブで**Auth0 Management API**を選択して`Authorize`
4. 必要なスコープを追加：
   - `read:users`
   - `delete:users`
5. 「Settings」タブで `AUTH0_MANAGEMENT_CLIENT_ID` と `AUTH0_MANAGEMENT_CLIENT_SECRET` を控える

#### Step 5: アプリケーション設定
1. Native Appの設定ページで以下を設定：
   - **Allowed Callback URLs**: 
     ```
     com.ehonnotane.ayu://ehonnotane.jp.auth0.com/ios/com.ehonnotane.ayu/callback
     ```
   - **Allowed Logout URLs**: 
     ```
     com.ehonnotane.ayu://ehonnotane.jp.auth0.com/ios/com.ehonnotane.ayu/callback
     ```
   - **Allowed Web Origins**: 必要に応じて設定

### 2. Google Cloud Consoleでの設定

#### Step 1: OAuth 2.0クライアントの作成
1. Google Cloud Console (https://console.cloud.google.com/) にアクセス
2. 「APIs & Services」→「Credentials」
3. 「Create Credentials」→「OAuth 2.0 Client IDs」
4. 以下の設定で作成：
   - **Application type**: `iOS`
   - **Bundle ID**: アプリのBundle ID
5. Client IDとClient Secretをコピー

#### Step 2: リダイレクトURIの設定
1. 作成したOAuth 2.0クライアントの設定ページを開く
2. 「Authorized redirect URIs」に以下を追加：
   - `https://ehonnotane.jp.auth0.com/login/callback`

---

## 環境変数の設定方法

### ローカル開発

`.env`ファイルを作成して設定：

```bash
# .envファイルを作成
cp AUTH0_ENV_EXAMPLE.txt .env

# .envファイルを編集
# 実際の値を設定してください
```

### Cloud Runデプロイ

```bash
gcloud run services update story-book-backend \
  --region=asia-northeast1 \
  --set-env-vars="AUTH0_DOMAIN=ehonnotane.jp.auth0.com,AUTH0_API_AUDIENCE=https://api.ehonnotane,AUTH0_NATIVE_CLIENT_ID=b1sTk9gTW2rjddFtvu0w7ZrsFYk2ldfh,GEMINI_API_KEY=AIza...,GCS_BUCKET_NAME=your-bucket-name"
```

---

## トラブルシューティング

### Q: Auth0の設定エラーが出る

```
Auth0設定エラー: AUTH0_DOMAINが設定されていません
```

**解決方法:**
1. 環境変数が正しく設定されているか確認
2. Auth0ダッシュボードでアプリケーションが正しく作成されているか確認

### Q: Googleログインが動かない

**原因**: Googleソーシャル接続が正しく設定されていない可能性があります。

**解決方法:**
1. Auth0ダッシュボードでGoogleソーシャル接続を確認
2. Google Cloud ConsoleでOAuth 2.0クライアントの設定を確認
3. リダイレクトURIが正しく設定されているか確認

### Q: リダイレクトURIエラーが発生する

```
Error: invalid_redirect_uri
```

**原因**: Auth0のAllowed Callback URLsが正しく設定されていない可能性があります。

**解決方法:**
1. Auth0ダッシュボードでNative Appの設定を確認
2. **Allowed Callback URLs**に以下が設定されているか確認：
   ```
   com.ehonnotane.ayu://ehonnotane.jp.auth0.com/ios/com.ehonnotane.ayu/callback
   ```
3. **Allowed Logout URLs**に以下が設定されているか確認：
   ```
   com.ehonnotane.ayu://ehonnotane.jp.auth0.com/ios/com.ehonnotane.ayu/callback
   ```

### Q: JWTトークンの検証エラー

**原因**: API Audienceが正しく設定されていない可能性があります。

**解決方法:**
1. Auth0ダッシュボードでAPIが正しく作成されているか確認
2. APIのIdentifierが`https://api.ehonnotane`と一致しているか確認

---

## セキュリティのベストプラクティス

1. **Client Secretは秘密に保つ**
   - Client Secretは絶対に公開しない
   - 環境変数として安全に管理

2. **Callback URLの制限**
   - 許可されたCallback URLのみを使用
   - 本番環境では適切なドメインを設定

3. **スコープの最小化**
   - 必要最小限のスコープのみを要求
   - ユーザーのプライバシーを保護

4. **定期的な監査**
   - Auth0ダッシュボードでアクセスログを確認
   - 異常なアクセスがないか監視
