-- Add child_id and page_count columns to story_settings table
ALTER TABLE story_settings ADD COLUMN child_id INTEGER REFERENCES children(id);
ALTER TABLE story_settings ADD COLUMN page_count INTEGER;
