-- Live Activityトークンテーブル作成
-- ActivityKit Push Notifications用のプッシュトークンを保存するテーブル

CREATE TABLE IF NOT EXISTS live_activity_tokens (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    push_token VARCHAR(512) NOT NULL,
    storybook_id BIGINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('Asia/Tokyo', now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('Asia/Tokyo', now())
);

-- インデックス
CREATE INDEX IF NOT EXISTS idx_live_activity_tokens_user_id ON live_activity_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_live_activity_tokens_storybook_id ON live_activity_tokens(storybook_id);
