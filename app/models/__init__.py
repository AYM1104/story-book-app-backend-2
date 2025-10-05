# すべてのモデルをインポートしてSQLAlchemyに認識させる
from .users.users import Users
from .images.images import UploadImages
from .story.story_setting import StorySetting
from .story.stroy_plot import StoryPlot
from .story.generated_story_book import GeneratedStoryBook

# Supabaseモデルもインポート
from .users.supabase_users import SupabaseUsers
from .images.supabase_images import SupabaseUploadImages
from .story.supabase_story_setting import SupabaseStorySetting
from .story.supabase_story_plot import SupabaseStoryPlot
from .story.supabase_generated_story_book import SupabaseGeneratedStoryBook