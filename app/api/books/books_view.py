from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.story.generated_story_book import GeneratedStoryBook
from app.schemas.story.generated_story_book import GeneratedStoryBookResponse
from typing import List, Optional
from datetime import datetime
import os

router = APIRouter(prefix="/books", tags=["books-view"])

def convert_file_path_to_url(file_path: Optional[str]) -> Optional[str]:
    """ローカルファイルパスをWebアクセス可能なURLに変換"""
    if not file_path:
        return None
    
    # 既にURLの場合はそのまま返す
    if file_path.startswith("http"):
        return file_path
    
    # 相対パスの場合はそのまま返す
    if file_path.startswith("/"):
        return file_path
    
    # ローカルファイルパスの場合
    if os.path.exists(file_path):
        # パスを相対パスに変換（/uploads/...）
        if "uploads" in file_path:
            # ファイルパスから相対パスを抽出
            parts = file_path.replace("\\", "/").split("/")
            uploads_index = parts.index("uploads") if "uploads" in parts else -1
            if uploads_index >= 0:
                # uploads以降の部分を取得
                relative_parts = parts[uploads_index:]
                relative_path = "/".join(relative_parts)
                return f"/{relative_path}"
    
    return None

# フロントエンド用のスキーマ
class BookSummaryResponse:
    """絵本一覧用のレスポンス"""
    def __init__(self, id: int, title: str, description: Optional[str], created_at: datetime):
        self.id = id
        self.title = title
        self.description = description
        self.created_at = created_at.isoformat()

class PageResponse:
    """ページ情報用のレスポンス"""
    def __init__(self, id: int, page_no: int, image_url: Optional[str], alt: str, text: str):
        self.id = id
        self.pageNo = page_no
        self.imageUrl = image_url
        self.alt = alt
        self.text = text

class BookDetailResponse:
    """絵本詳細用のレスポンス"""
    def __init__(self, id: int, title: str, description: Optional[str], pages: List[PageResponse], created_at: datetime):
        self.id = id
        self.title = title
        self.description = description
        self.pages = pages
        self.created_at = created_at.isoformat()

@router.get("/")
async def get_books_list(
    limit: Optional[int] = 20,
    cursor: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """絵本一覧を取得するエンドポイント（フロントエンド用）"""
    
    try:
        # クエリを構築
        query = db.query(GeneratedStoryBook).order_by(GeneratedStoryBook.created_at.desc())
        
        # カーソルベースのページネーション（簡単な実装）
        if cursor:
            query = query.filter(GeneratedStoryBook.id < cursor)
        
        # 件数制限
        if limit:
            query = query.limit(limit + 1)  # 1つ多く取得してhasMoreを判定
        
        storybooks = query.all()
        
        # hasMoreの判定
        has_more = len(storybooks) > limit if limit else False
        if has_more:
            storybooks = storybooks[:-1]  # 最後の1件を除外
        
        # レスポンス形式に変換
        books = []
        for storybook in storybooks:
            books.append(BookSummaryResponse(
                id=storybook.id,
                title=storybook.title,
                description=storybook.description,
                created_at=storybook.created_at
            ))
        
        # 次のカーソルを計算
        next_cursor = None
        if has_more and storybooks:
            next_cursor = str(storybooks[-1].id)
        
        return {
            "books": [book.__dict__ for book in books],
            "hasMore": has_more,
            "nextCursor": next_cursor
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"絵本一覧の取得に失敗しました: {str(e)}"
        )

@router.get("/{book_id}")
async def get_book_detail(
    book_id: int,
    db: Session = Depends(get_db)
):
    """絵本詳細を取得するエンドポイント（フロントエンド用）"""
    
    try:
        storybook = db.query(GeneratedStoryBook).filter(
            GeneratedStoryBook.id == book_id
        ).first()
        
        if not storybook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"絵本 ID {book_id} が見つかりません"
            )
        
        # 5ページの情報を配列形式に変換
        pages = []
        page_texts = [storybook.page_1, storybook.page_2, storybook.page_3, storybook.page_4, storybook.page_5]
        page_image_urls = [
            storybook.page_1_image_url, 
            storybook.page_2_image_url, 
            storybook.page_3_image_url, 
            storybook.page_4_image_url, 
            storybook.page_5_image_url
        ]
        
        for i, (text, image_url) in enumerate(zip(page_texts, page_image_urls), 1):
            if text:  # テキストが存在するページのみ追加
                # 画像URLをWebアクセス可能な形式に変換
                web_image_url = convert_file_path_to_url(image_url)
                
                pages.append(PageResponse(
                    id=book_id * 100 + i,  # 一意のIDを生成
                    page_no=i,
                    image_url=web_image_url,
                    alt=f"{storybook.title} - ページ{i}",
                    text=text
                ))
        
        book_detail = BookDetailResponse(
            id=storybook.id,
            title=storybook.title,
            description=storybook.description,
            pages=pages,
            created_at=storybook.created_at
        )
        
        return book_detail.__dict__
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"絵本詳細の取得に失敗しました: {str(e)}"
        )
