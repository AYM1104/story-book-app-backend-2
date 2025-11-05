from typing import Dict, Tuple
from app.models.credits.subscription import PlanType

class PricingService:
    """価格計算サービス
    
    pricing.mdに定義された価格表に基づいて計算を行う
    """
    
    # 合計ページ数（表紙込み）→ 消費クレジット
    COST_TABLE: Dict[int, int] = {
        4: 80,   # 3ページ（物語）+ 1ページ（表紙）
        6: 120,  # 5ページ（物語）+ 1ページ（表紙）
        8: 150,  # 7ページ（物語）+ 1ページ（表紙）
        11: 200  # 10ページ（物語）+ 1ページ（表紙）
    }
    
    # プランごとの許可される物語ページ数
    ALLOWED_PAGES: Dict[PlanType, list[int]] = {
        PlanType.FREE: [3, 5],
        PlanType.STARTER: [3, 5],
        PlanType.PLUS: [3, 5, 7, 10],
        PlanType.PREMIUM: [3, 5, 7, 10]
    }
    
    @staticmethod
    def calculate_total_pages(story_pages: int) -> int:
        """物語ページ数から合計ページ数（表紙込み）を計算
        
        Args:
            story_pages: 物語ページ数（3, 5, 7, 10のいずれか）
            
        Returns:
            合計ページ数（表紙込み）
        """
        return story_pages + 1
    
    @staticmethod
    def get_required_credits(story_pages: int) -> int:
        """必要クレジット数を取得
        
        Args:
            story_pages: 物語ページ数（3, 5, 7, 10のいずれか）
            
        Returns:
            必要クレジット数
            
        Raises:
            ValueError: 無効なページ数の場合
        """
        total_pages = PricingService.calculate_total_pages(story_pages)
        
        if total_pages not in PricingService.COST_TABLE:
            raise ValueError(f"無効なページ数: story_pages={story_pages}, total_pages={total_pages}")
        
        return PricingService.COST_TABLE[total_pages]
    
    @staticmethod
    def is_allowed_for_plan(story_pages: int, plan: PlanType) -> bool:
        """プランで指定されたページ数が許可されているか確認
        
        Args:
            story_pages: 物語ページ数
            plan: プランタイプ
            
        Returns:
            許可されている場合True
        """
        allowed = PricingService.ALLOWED_PAGES.get(plan, [])
        return story_pages in allowed
    
    @staticmethod
    def generate_quote(story_pages: int) -> Dict[str, int]:
        """クレジット見積もりを生成
        
        Args:
            story_pages: 物語ページ数
            
        Returns:
            {
                "required_credits": 必要クレジット数,
                "total_pages": 合計ページ数（表紙込み）
            }
            
        Raises:
            ValueError: 無効なページ数の場合
        """
        total_pages = PricingService.calculate_total_pages(story_pages)
        required_credits = PricingService.get_required_credits(story_pages)
        
        return {
            "required_credits": required_credits,
            "total_pages": total_pages
        }

