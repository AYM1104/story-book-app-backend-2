# Story Book Backend - Cloud Run デプロイスクリプト (PowerShell版)

param(
    [string]$ProjectId = "",
    [string]$Region = "asia-northeast1",
    [string]$ServiceName = "story-book-backend"
)

# エラー時にスクリプトを停止
$ErrorActionPreference = "Stop"

# 色付きの出力用
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

Write-ColorOutput "🚀 Story Book Backend - Cloud Run デプロイスクリプト" "Green"
Write-Host ""

# プロジェクトIDの確認
if ([string]::IsNullOrEmpty($ProjectId)) {
    Write-ColorOutput "❌ エラー: ProjectIdパラメータが設定されていません" "Red"
    Write-ColorOutput "使用方法: .\deploy.ps1 -ProjectId 'your-project-id'" "Yellow"
    exit 1
}

$ImageName = "gcr.io/$ProjectId/$ServiceName"

Write-ColorOutput "📋 デプロイ設定:" "Yellow"
Write-ColorOutput "  プロジェクトID: $ProjectId"
Write-ColorOutput "  リージョン: $Region"
Write-ColorOutput "  サービス名: $ServiceName"
Write-ColorOutput "  イメージ名: $ImageName"
Write-Host ""

# 確認
$confirmation = Read-Host "デプロイを続行しますか？ (y/N)"
if ($confirmation -ne 'y' -and $confirmation -ne 'Y') {
    Write-ColorOutput "デプロイをキャンセルしました" "Yellow"
    exit 1
}

try {
    Write-ColorOutput "🔧 必要なAPIの有効化..." "Green"
    gcloud services enable cloudbuild.googleapis.com
    gcloud services enable run.googleapis.com
    gcloud services enable containerregistry.googleapis.com
    gcloud services enable cloudresourcemanager.googleapis.com

    Write-ColorOutput "🔨 Dockerイメージのビルド..." "Green"
    docker build -t $ImageName .

    Write-ColorOutput "📤 イメージをGoogle Container Registryにプッシュ..." "Green"
    docker push $ImageName

    Write-ColorOutput "🚀 Cloud Runにデプロイ..." "Green"
    gcloud run deploy $ServiceName --image $ImageName --region $Region --platform managed --allow-unauthenticated --port 8080 --memory 2Gi --cpu 2 --max-instances 10 --min-instances 0 --timeout 300

    Write-ColorOutput "✅ デプロイが完了しました！" "Green"
    Write-Host ""

    # サービスのURLを取得
    $ServiceUrl = gcloud run services describe $ServiceName --region=$Region --format="value(status.url)"
    Write-ColorOutput "🌐 サービスURL: $ServiceUrl" "Green"
    Write-Host ""

    # ヘルスチェック
    Write-ColorOutput "🔍 ヘルスチェックを実行中..." "Yellow"
    try {
        $response = Invoke-WebRequest -Uri $ServiceUrl -TimeoutSec 10
        if ($response.StatusCode -eq 200) {
            Write-ColorOutput "✅ サービスが正常に動作しています" "Green"
        } else {
            Write-ColorOutput "❌ サービスが期待したレスポンスを返しませんでした (ステータス: $($response.StatusCode))" "Red"
        }
    } catch {
        Write-ColorOutput "❌ サービスへの接続に失敗しました: $($_.Exception.Message)" "Red"
        Write-ColorOutput "ログを確認してください:" "Yellow"
        Write-ColorOutput "gcloud run services logs read $ServiceName --region=$Region" "Cyan"
    }

    Write-Host ""
    Write-ColorOutput "🎉 デプロイが完了しました！" "Green"
    Write-ColorOutput "💡 次のステップ:" "Yellow"
    Write-ColorOutput "  1. 環境変数の設定: gcloud run services update $ServiceName --region=$Region --set-env-vars=`"KEY=VALUE`"" "Cyan"
    Write-ColorOutput "  2. ログの確認: gcloud run services logs read $ServiceName --region=$Region" "Cyan"
    Write-ColorOutput "  3. サービス詳細: gcloud run services describe $ServiceName --region=$Region" "Cyan"

} catch {
    Write-ColorOutput "❌ デプロイ中にエラーが発生しました: $($_.Exception.Message)" "Red"
    exit 1
}