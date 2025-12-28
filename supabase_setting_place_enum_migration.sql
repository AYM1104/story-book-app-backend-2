-- setting_place列をENUM型に変更するためのマイグレーションSQL
-- SupabaseのSQL Editorで実行してください

-- 1. ENUM型を作成
CREATE TYPE setting_place_enum AS ENUM ('公園', '家', '森', '海', '山', '宇宙', '学校', 'まち', '庭');

-- 2. 既存のデータをENUM値に変換（英語値がある場合は日本語にマッピング）
-- まず、一時的な列を作成してデータを変換
ALTER TABLE story_settings ADD COLUMN setting_place_new setting_place_enum;

-- 既存データの変換（英語値がある場合は日本語にマッピング）
UPDATE story_settings 
SET setting_place_new = CASE
    WHEN setting_place IN ('公園', 'park') THEN '公園'::setting_place_enum
    WHEN setting_place IN ('家', 'house', 'おうち') THEN '家'::setting_place_enum
    WHEN setting_place IN ('森', 'forest') THEN '森'::setting_place_enum
    WHEN setting_place IN ('海', 'sea') THEN '海'::setting_place_enum
    WHEN setting_place IN ('山', 'mountain') THEN '山'::setting_place_enum
    WHEN setting_place IN ('宇宙', 'space') THEN '宇宙'::setting_place_enum
    WHEN setting_place IN ('学校', 'school') THEN '学校'::setting_place_enum
    WHEN setting_place IN ('まち', 'city') THEN 'まち'::setting_place_enum
    WHEN setting_place IN ('庭', 'garden') THEN '庭'::setting_place_enum
    ELSE NULL
END;

-- 3. 元の列を削除
ALTER TABLE story_settings DROP COLUMN setting_place;

-- 4. 新しい列を元の名前にリネーム
ALTER TABLE story_settings RENAME COLUMN setting_place_new TO setting_place;

-- 5. コメントを追加（オプション）
COMMENT ON COLUMN story_settings.setting_place IS '物語の舞台となる場所（公園、海、山、宇宙など）';

