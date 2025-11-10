# 機能フォルダ構成案メモ

今後、機能ごとにコードを垂直スライスで整理していく際のフォルダ構成イメージをメモしておく。

```
app/
  features/
    auth/
      api/
      schemas/
      services/
      config/
    story_creation/
      api/
      schemas/
      services/
      models/
      config/
    story_questions/
      api/
      schemas/
      services/
    image_upload/
      api/
      schemas/
      services/
      config/
    credits/
      api/
      schemas/
      services/
    pricing/
      api/
      schemas/
      services/
    child_management/
      api/
      schemas/
      services/
  shared/
    core_config/
    database/
    utils/
    external_clients/
```

- `features/` 配下に機能単位のパッケージを配置し、ドメインごとに API・スキーマ・サービスなどをまとめる。
- 共通処理やインフラ周りは `shared/`（または `common/`）へ置き、各機能から参照する想定。
- 実際の移行は既存コードに影響が出ないよう段階的に進める。

