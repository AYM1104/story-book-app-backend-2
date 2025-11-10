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

#### Step 3.5: Appleソーシャル接続の設定
1. 「Authentication」→「Social」→「Create Connection」
2. 「Apple」を選択
3. Apple接続の設定画面で以下の項目を設定：

   **Client ID**（オプション）:
   - Auth0のClient IDを入力（空白の場合はAuth0のdev keysが使用されます）
   - 通常は空白のままで問題ありません

   **Client Secret Signing Key**（必須）:
   - Apple Developerで作成したPrivate Key（.p8ファイルの内容）を貼り付け
   - 取得方法: Apple Developer → Certificates, Identifiers & Profiles → Keys → 作成したKey → Download → .p8ファイルを開いて内容をコピー
   - **重要**: このフィールドは既存の値が表示されないため、新規作成時は必ず入力が必要です

   **Apple Team ID**（必須）:
   - Apple DeveloperのTeam IDを入力
   - 取得方法: Apple Developer → Membership → Team IDをコピー
   - 形式: `XXXXXXXXXX`（10文字の英数字）

   **Key ID**（必須）:
   - Apple Developerで作成したKey IDを入力
   - 取得方法: Apple Developer → Certificates, Identifiers & Profiles → Keys → 作成したKey → Key IDをコピー
   - 形式: `XXXXXXXXXX`（10文字の英数字）

4. **重要**: 「Applications」タブを開き、Native App（`b1sTk9gTW2rjddFtvu0w7ZrsFYk2ldfh`）のチェックボックスをオンにする
   - この設定を忘れると「the connection is not enabled」エラーが発生します
5. 「Save」をクリックして設定を保存

**⚠️ 注意**: 
- Apple接続を有効化しないと、アプリで「the connection is not enabled」エラーが発生します
- Apple DeveloperでService IDとKeyを作成する必要があります（詳細は後述）

#### Step 3.7: X（Twitter）ソーシャル接続の設定
1. 「Authentication」→「Social」→「Create Connection」
2. 「Twitter」を選択
3. X（Twitter）接続の設定画面で以下の項目を設定：

   **API Key**（必須）:
   - Twitter Developer Portalで作成したアプリのAPI Keyを入力
   - 取得方法: Twitter Developer Portal → Projects & Apps → 作成したApp → Keys and tokens → API Keyをコピー

   **API Secret**（必須）:
   - Twitter Developer Portalで作成したアプリのAPI Secretを入力
   - 取得方法: Twitter Developer Portal → Projects & Apps → 作成したApp → Keys and tokens → API Secretをコピー
   - **重要**: この値は秘密に保持してください

4. **重要**: 「Applications」タブを開き、Native App（`b1sTk9gTW2rjddFtvu0w7ZrsFYk2ldfh`）のチェックボックスをオンにする
   - この設定を忘れると「the connection is not enabled」エラーが発生します
5. 「Save」をクリックして設定を保存

**⚠️ 注意**: 
- X（Twitter）接続を有効化しないと、アプリで「the connection is not enabled」エラーが発生します
- Twitter Developer Portalでアプリを作成する必要があります（詳細は後述）

#### Step 3.6: LINEソーシャル接続の設定
1. 「Authentication」→「Social」→「Create Connection」
2. 「LINE」を選択
3. LINE接続の設定画面で以下の項目を設定：

   **Channel ID**（必須）:
   - LINE Developersで作成したチャネルのChannel IDを入力
   - 取得方法: LINE Developers Console → チャネル → Basic settings → Channel IDをコピー

   **Channel Secret**（必須）:
   - LINE Developersで作成したチャネルのChannel Secretを入力
   - 取得方法: LINE Developers Console → チャネル → Basic settings → Channel Secretをコピー
   - **重要**: この値は秘密に保持してください

4. **重要**: 「Applications」タブを開き、Native App（`b1sTk9gTW2rjddFtvu0w7ZrsFYk2ldfh`）のチェックボックスをオンにする
   - この設定を忘れると「the connection is not enabled」エラーが発生します
5. 「Save」をクリックして設定を保存

**⚠️ 注意**: 
- LINE接続を有効化しないと、アプリで「the connection is not enabled」エラーが発生します
- LINE Developersでチャネルを作成する必要があります（詳細は後述）

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

### 3. Apple Developerでの設定（Apple Sign In用）

Apple Sign Inを使用するには、Apple Developerで以下の設定が必要です：

#### Step 1: Service IDの作成
1. Apple Developer (https://developer.apple.com/) にログイン
2. 「Certificates, Identifiers & Profiles」→「Identifiers」→「+」をクリック
3. 「Services IDs」を選択して「Continue」
4. 以下の情報を入力：
   - **Description**: `Story Book App`（任意の名前）
   - **Identifier**: `com.ehonnotane.ayu`（アプリのBundle IDと一致させる）
5. 「Sign In with Apple」にチェックを入れて「Configure」
6. 「Primary App ID」でアプリのApp IDを選択
7. 「Return URLs」に以下を追加：
   - `https://ehonnotane.jp.auth0.com/login/callback`
8. 「Save」→「Continue」→「Register」

#### Step 2: Keyの作成
1. 「Certificates, Identifiers & Profiles」→「Keys」→「+」をクリック
2. 以下の情報を入力：
   - **Key Name**: `Auth0 Apple Sign In Key`（任意の名前）
   - **Sign In with Apple**にチェックを入れる
3. 「Continue」→「Register」
4. **重要**: Key IDをメモする（後で確認できないため）
5. 「Download」をクリックして`.p8`ファイルをダウンロード
   - **重要**: このファイルは1回しかダウンロードできません。安全に保管してください

#### Step 3: Team IDの確認
1. Apple Developer → 「Membership」
2. 「Team ID」をコピー（10文字の英数字）

#### Step 4: 取得した情報をAuth0に設定
上記で取得した以下の情報を、Auth0のApple接続設定画面に入力：
- **Apple Team ID**: Step 3で取得したTeam ID
- **Key ID**: Step 2で取得したKey ID
- **Client Secret Signing Key**: Step 2でダウンロードした`.p8`ファイルの内容（テキストエディタで開いて全体をコピー）

### 5. Twitter Developer Portalでの設定（X（Twitter）ログイン用）

X（Twitter）ログインを使用するには、Twitter Developer Portalで以下の設定が必要です：

#### Step 1: Twitter Developerアカウントの作成
1. Twitter Developer Portal (https://developer.twitter.com/) にアクセス
2. Twitterアカウントでログイン
3. Developerアカウントの申請（必要に応じて）

#### Step 2: プロジェクトとアプリの作成
1. Twitter Developer Portalにログイン
2. 「Projects & Apps」→「+ Create Project」をクリック
3. プロジェクト名を入力して「Next」をクリック
4. アプリ名を入力して「Next」をクリック
5. アプリの用途を選択（例: Making a bot）して「Next」をクリック
6. 「Create」をクリックしてプロジェクトとアプリを作成

#### Step 3: OAuth 2.0設定
1. 作成したアプリを選択
2. 「Settings」タブを開く
3. 「App permissions」で「Read」を選択（必要に応じて「Read and write」も選択可能）
4. 「Callback URI / Redirect URL」に以下を追加：
   - `https://ehonnotane.jp.auth0.com/login/callback`
5. 「Website URL」にアプリのURLを入力（例: `https://ehonnotane.jp`）
6. 「Save」をクリック

#### Step 4: API KeyとAPI Secretの取得
1. 作成したアプリの「Keys and tokens」タブを開く
2. 「API Key」と「API Secret」をコピー
   - **重要**: API Secretは一度しか表示されません。安全に保管してください
3. これらの値をAuth0ダッシュボードのTwitter接続設定に入力

#### Step 5: 取得した情報をAuth0に設定
上記で取得した以下の情報を、Auth0のTwitter接続設定画面に入力：
- **API Key**: Step 4で取得したAPI Key
- **API Secret**: Step 4で取得したAPI Secret

---

### 4. LINE Developersでの設定（LINEログイン用）

LINEログインを使用するには、LINE Developersで以下の設定が必要です：

#### Step 1: プロバイダーの作成
1. LINE Developers Console (https://developers.line.biz/console/) にログイン
2. 「プロバイダーを作成」をクリック
3. プロバイダー名を入力して「作成」をクリック

#### Step 2: チャネルの作成
1. 作成したプロバイダーを選択
2. 「チャネルを作成」をクリック
3. 「LINE Login」を選択して「次へ」
4. 以下の情報を入力：
   - **チャネル名**: `Story Book App`（任意の名前）
   - **チャネル説明**: 任意の説明
   - **アプリタイプ**: `Web app` ⚠️ **重要**: ネイティブアプリでも「Web app」を選択してください
   - **メールアドレス**: 連絡先メールアドレス
5. 「作成」をクリック

**⚠️ 重要**: 
- iOSネイティブアプリでも、Auth0を経由する場合は「Web app」タイプのチャネルを作成する必要があります
- 「iOS app」や「Android app」を選択するとCallback URLの設定項目が表示されません
- Auth0が中間プロキシとして機能するため、LINE → Auth0 → iOSアプリという流れになります

#### Step 3: チャネル設定
1. 作成したチャネルを選択
2. 「Basic settings」タブで以下を確認・設定：
   - **Channel ID**: 後でAuth0に設定するため、コピーしておく
   - **Channel Secret**: 後でAuth0に設定するため、コピーしておく
     - **重要**: Channel Secretは一度しか表示されません。安全に保管してください

#### Step 4: Callback URLの設定
1. 「LINE Login settings」タブを開く
2. 「Callback URL」欄に以下を追加：
   - `https://ehonnotane.jp.auth0.com/login/callback`
3. 「保存」をクリック

**⚠️ 重要**: 
- Callback URLはLINE Developers Consoleで設定します
- このURLは、LINE認証後にAuth0にリダイレクトするために必要です
- 複数のCallback URLを設定する場合は、1行に1つずつ入力してください
- 「Web app」タイプのチャネルを作成した場合のみ、この設定項目が表示されます

#### Step 5: 取得した情報をAuth0に設定
上記で取得した以下の情報を、Auth0のLINE接続設定画面に入力：
- **Channel ID**: Step 3で取得したChannel ID
- **Channel Secret**: Step 3で取得したChannel Secret

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

### Q: Apple Sign Inで「the connection is not enabled」エラーが発生する

**原因**: Auth0ダッシュボードでApple接続が有効になっていない、またはNative Appに接続が紐付けられていない可能性があります。

**解決方法:**
1. Auth0ダッシュボードにログイン
2. 「Authentication」→「Social」→「Apple」を選択
3. Apple接続が作成されているか確認（なければ作成）
4. **重要**: 「Applications」タブを開き、Native App（`b1sTk9gTW2rjddFtvu0w7ZrsFYk2ldfh`）が有効になっているか確認
   - チェックボックスがオフになっている場合は、オンにして「Save」をクリック
5. Apple Developerで作成したService ID、Team ID、Key ID、Private Keyが正しく設定されているか確認
6. 設定を保存後、数分待ってから再度試す（設定の反映に時間がかかる場合があります）

**エラーメッセージ例:**
```
❌ Apple Sign Inエラー詳細: An unexpected error occurred. CAUSE: the connection is not enabled.
```

### Q: X（Twitter）ログインで「the connection is not enabled」エラーが発生する

**原因**: Auth0ダッシュボードでX（Twitter）接続が有効になっていない、またはNative Appに接続が紐付けられていない可能性があります。

**解決方法:**
1. Auth0ダッシュボードにログイン
2. 「Authentication」→「Social」→「Twitter」を選択
3. X（Twitter）接続が作成されているか確認（なければ作成）
4. **重要**: 「Applications」タブを開き、Native App（`b1sTk9gTW2rjddFtvu0w7ZrsFYk2ldfh`）が有効になっているか確認
   - チェックボックスがオフになっている場合は、オンにして「Save」をクリック
5. Twitter Developer Portalで作成したAPI KeyとAPI Secretが正しく設定されているか確認
6. Twitter Developer PortalのCallback URLに`https://ehonnotane.jp.auth0.com/login/callback`が設定されているか確認
7. 設定を保存後、数分待ってから再度試す（設定の反映に時間がかかる場合があります）

**エラーメッセージ例:**
```
❌ X（Twitter）ログインエラー詳細: An unexpected error occurred. CAUSE: the connection is not enabled.
```

### Q: LINEログインで「the connection is not enabled」エラーが発生する

**原因**: Auth0ダッシュボードでLINE接続が有効になっていない、またはNative Appに接続が紐付けられていない可能性があります。

**解決方法:**
1. Auth0ダッシュボードにログイン
2. 「Authentication」→「Social」→「LINE」を選択
3. LINE接続が作成されているか確認（なければ作成）
4. **重要**: 「Applications」タブを開き、Native App（`b1sTk9gTW2rjddFtvu0w7ZrsFYk2ldfh`）が有効になっているか確認
   - チェックボックスがオフになっている場合は、オンにして「Save」をクリック
5. LINE Developersで作成したChannel IDとChannel Secretが正しく設定されているか確認
6. LINE DevelopersのCallback URLに`https://ehonnotane.jp.auth0.com/login/callback`が設定されているか確認
7. 設定を保存後、数分待ってから再度試す（設定の反映に時間がかかる場合があります）

**エラーメッセージ例:**
```
❌ LINEログインエラー詳細: An unexpected error occurred. CAUSE: the connection is not enabled.
```

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
