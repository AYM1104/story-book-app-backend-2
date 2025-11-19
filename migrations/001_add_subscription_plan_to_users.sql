-- Add subscription_plan column to users table
ALTER TABLE users 
ADD COLUMN subscription_plan text NOT NULL DEFAULT 'FREE';

-- Add check constraint to ensure data integrity matches the Enum
ALTER TABLE users 
ADD CONSTRAINT check_subscription_plan_values 
CHECK (subscription_plan IN ('FREE', 'STARTER', 'PLUS', 'PREMIUM'));

-- Comment on the column
COMMENT ON COLUMN users.subscription_plan IS '現在のサブスクリプションプラン';
