#!/usr/bin/env python3
"""
usersテーブルにbalanceカラムを追加し、既存データをマイグレーションするスクリプト

使用方法:
python migrate_add_balance_to_users.py
"""

from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database.supabase_session import engine, get_supabase_db
from app.models.users.users import Users
from app.models.credits.credit_ledger import CreditLedger
from sqlalchemy import func

def migrate_users_balance():
    """usersテーブルにbalanceカラムを追加し、既存データをマイグレーション"""
    
    print("=== usersテーブルにbalanceカラムを追加するマイグレーション開始 ===")
    
    # データベース接続
    with engine.connect() as conn:
        try:
            # 1. balanceカラムが存在するか確認
            check_column_query = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'balance'
            """)
            result = conn.execute(check_column_query).fetchone()
            
            if result:
                print("✓ balanceカラムは既に存在します")
            else:
                # 2. balanceカラムを追加
                print("balanceカラムを追加中...")
                add_column_query = text("""
                    ALTER TABLE users 
                    ADD COLUMN balance INTEGER NOT NULL DEFAULT 0
                """)
                conn.execute(add_column_query)
                conn.commit()
                print("✓ balanceカラムを追加しました")
            
            # 3. 既存ユーザーの残高を台帳から計算して更新
            print("\n既存ユーザーの残高を台帳から計算して更新中...")
            
            # セッションを作成
            db = next(get_supabase_db())
            
            try:
                # すべてのユーザーを取得
                users = db.query(Users).all()
                print(f"対象ユーザー数: {len(users)}")
                
                updated_count = 0
                for user in users:
                    # 台帳から残高を計算
                    result = db.query(func.sum(CreditLedger.delta)).filter(
                        CreditLedger.user_id == user.id
                    ).scalar()
                    
                    calculated_balance = int(result) if result is not None else 0
                    
                    # 残高が異なる場合のみ更新
                    if user.balance != calculated_balance:
                        old_balance = user.balance if user.balance is not None else 0
                        user.balance = calculated_balance
                        updated_count += 1
                        print(f"  ユーザー {user.id}: {old_balance} → {calculated_balance}")
                
                db.commit()
                print(f"\n✓ {updated_count}件のユーザー残高を更新しました")
                
            except Exception as e:
                db.rollback()
                print(f"❌ エラーが発生しました: {e}")
                raise
            finally:
                db.close()
            
            print("\n=== マイグレーション完了 ===")
            
        except Exception as e:
            print(f"❌ マイグレーションエラー: {e}")
            conn.rollback()
            raise

if __name__ == "__main__":
    migrate_users_balance()

