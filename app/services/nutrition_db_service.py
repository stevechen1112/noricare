"""
Taiwan Food Nutrition Database Service (Phase 1 MVP)
=====================================================
獨立的營養查詢服務，不影響現有 AI 報告流程。

設計原則：
- 隔離策略：完全獨立運作，失敗不影響主系統
- 精簡欄位：只保留 5 核心營養素（熱量、蛋白質、碳水、脂肪、鈉）
- 可驗證性：提供匹配率統計，便於評估價值

成功指標：
- Top 20 常見食物匹配率 ≥ 80%
- 查詢響應時間 < 100ms
"""

import pandas as pd
import os
from typing import Optional, List, Dict, Any
from functools import lru_cache
import re
import logging

logger = logging.getLogger(__name__)


class NutritionDBService:
    """台灣食品營養成分資料庫服務 (Phase 1 MVP)"""
    
    # 核心營養欄位（精簡為 5 項）
    CORE_FIELDS = {
        '樣品名稱': 'name',
        '食品分類': 'category', 
        '熱量(kcal)': 'calories',
        '粗蛋白(g)': 'protein',
        '總碳水化合物(g)': 'carbs',
        '粗脂肪(g)': 'fat',
        '鈉(mg)': 'sodium',
        '膳食纖維(g)': 'fiber',
        '鉀(mg)': 'potassium',  # 腎功能患者重要
    }
    
    # Top 20 常見食物名稱映射表（用於模糊匹配）
    FOOD_ALIASES = {
        # 主食類
        '白飯': ['米飯', '白米飯', '蓬萊米飯', '稉米飯'],
        '糙米飯': ['糙米', '胚芽米飯'],
        '麵條': ['麵', '拉麵', '陽春麵', '意麵'],
        '吐司': ['白吐司', '土司', '麵包'],
        '饅頭': ['白饅頭', '刈包皮'],
        
        # 蛋白質類
        '雞胸肉': ['雞胸', '雞里肌', '雞柳'],
        '雞蛋': ['蛋', '全蛋', '雞蛋'],
        '豆腐': ['板豆腐', '嫩豆腐', '傳統豆腐'],
        '鮭魚': ['鮭', '三文魚'],
        '豬肉': ['瘦豬肉', '豬里肌', '豬腿肉'],
        
        # 蔬菜類
        '菠菜': ['菠菜', '波菜'],
        '高麗菜': ['甘藍', '包心菜', '捲心菜'],
        '花椰菜': ['青花菜', '綠花椰', '西蘭花'],
        '番茄': ['蕃茄', '大番茄', '牛番茄'],
        '紅蘿蔔': ['胡蘿蔔', '紅蘿蔔'],
        
        # 水果類
        '蘋果': ['蘋果', '富士蘋果'],
        '香蕉': ['香蕉', '芭蕉', '北蕉'],  # 台灣稱「北蕉」
        '柳橙': ['柳丁', '橙', '甜橙'],
        '芭樂': ['番石榴', '芭樂'],
        '奇異果': ['奇異果', '獼猴桃'],
    }
    
    def __init__(self, csv_path: Optional[str] = None):
        """初始化服務"""
        if csv_path is None:
            # 預設路徑 - 支援多種執行環境
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            csv_path = os.path.join(base_dir, '食品營養成分資料庫2024UPDATE2_clean.csv')
            
            # 如果預設路徑不存在，嘗試從工作目錄找
            if not os.path.exists(csv_path):
                csv_path = '食品營養成分資料庫2024UPDATE2_clean.csv'
        
        self.csv_path = csv_path
        self._df: Optional[pd.DataFrame] = None
        self._simplified_df: Optional[pd.DataFrame] = None
        self._search_stats = {
            'total_queries': 0,
            'successful_matches': 0,
            'failed_matches': 0,
        }
    
    @property
    def df(self) -> pd.DataFrame:
        """延遲載入完整資料"""
        if self._df is None:
            self._load_data()
        return self._df
    
    @property
    def simplified_df(self) -> pd.DataFrame:
        """精簡版資料（只有核心欄位）"""
        if self._simplified_df is None:
            self._create_simplified_view()
        return self._simplified_df
    
    def _load_data(self):
        """載入 CSV 資料"""
        try:
            self._df = pd.read_csv(self.csv_path, encoding='utf-8')
            logger.info(f"✅ 載入營養資料庫: {len(self._df)} 筆食物")
        except Exception as e:
            logger.error(f"❌ 載入營養資料庫失敗: {e}")
            self._df = pd.DataFrame()
    
    def _create_simplified_view(self):
        """建立精簡視圖（只保留核心欄位）"""
        available_cols = [col for col in self.CORE_FIELDS.keys() if col in self.df.columns]
        self._simplified_df = self.df[available_cols].copy()
        
        # 重新命名為英文（方便 API 使用）
        rename_map = {k: v for k, v in self.CORE_FIELDS.items() if k in available_cols}
        self._simplified_df = self._simplified_df.rename(columns=rename_map)
        
        # 清理數值欄位（處理空值）
        numeric_cols = ['calories', 'protein', 'carbs', 'fat', 'sodium', 'fiber', 'potassium']
        for col in numeric_cols:
            if col in self._simplified_df.columns:
                self._simplified_df[col] = pd.to_numeric(
                    self._simplified_df[col], errors='coerce'
                ).fillna(0)
        
        logger.info(f"✅ 精簡視圖建立完成: {len(self._simplified_df)} 筆, {len(available_cols)} 欄")
    
    def search(
        self, 
        query: str, 
        limit: int = 5,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        搜尋食物營養資訊
        
        Args:
            query: 食物名稱（支援模糊匹配）
            limit: 回傳筆數上限
            category: 限定食品分類（可選）
            
        Returns:
            營養資訊列表
        """
        self._search_stats['total_queries'] += 1
        
        df = self.simplified_df.copy()
        
        # 類別過濾
        if category and 'category' in df.columns:
            df = df[df['category'].str.contains(category, na=False)]
        
        # 1. 精確匹配
        exact_matches = df[df['name'] == query]
        if not exact_matches.empty:
            self._search_stats['successful_matches'] += 1
            return self._format_results(exact_matches.head(limit))
        
        # 2. 別名匹配
        expanded_queries = self._expand_aliases(query)
        for alias in expanded_queries:
            alias_matches = df[df['name'].str.contains(alias, na=False, regex=False)]
            if not alias_matches.empty:
                self._search_stats['successful_matches'] += 1
                return self._format_results(alias_matches.head(limit))
        
        # 3. 模糊匹配（包含查詢字串）
        fuzzy_matches = df[df['name'].str.contains(query, na=False, regex=False)]
        if not fuzzy_matches.empty:
            self._search_stats['successful_matches'] += 1
            return self._format_results(fuzzy_matches.head(limit))
        
        # 4. 分詞匹配（拆解查詢）
        if len(query) >= 2:
            for i in range(len(query) - 1):
                partial = query[i:i+2]
                partial_matches = df[df['name'].str.contains(partial, na=False, regex=False)]
                if not partial_matches.empty:
                    self._search_stats['successful_matches'] += 1
                    return self._format_results(partial_matches.head(limit))
        
        # 無匹配
        self._search_stats['failed_matches'] += 1
        return []
    
    def _expand_aliases(self, query: str) -> List[str]:
        """展開食物別名"""
        aliases = [query]
        
        # 檢查是否在別名表中
        for canonical, alias_list in self.FOOD_ALIASES.items():
            if query == canonical or query in alias_list:
                aliases.extend([canonical] + alias_list)
                break
        
        return list(set(aliases))
    
    def _format_results(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """格式化搜尋結果"""
        results = []
        for _, row in df.iterrows():
            result = {
                'name': row.get('name', ''),
                'category': row.get('category', ''),
                'per_100g': {
                    'calories': round(float(row.get('calories', 0)), 1),
                    'protein': round(float(row.get('protein', 0)), 1),
                    'carbs': round(float(row.get('carbs', 0)), 1),
                    'fat': round(float(row.get('fat', 0)), 1),
                    'sodium': round(float(row.get('sodium', 0)), 1),
                    'fiber': round(float(row.get('fiber', 0)), 1),
                    'potassium': round(float(row.get('potassium', 0)), 1),
                }
            }
            results.append(result)
        return results
    
    def calculate_nutrients(
        self, 
        food_name: str, 
        grams: float = 100
    ) -> Optional[Dict[str, Any]]:
        """
        計算指定克數的營養成分
        
        Args:
            food_name: 食物名稱
            grams: 克數（預設 100g）
            
        Returns:
            營養成分字典（按比例計算）
        """
        results = self.search(food_name, limit=1)
        if not results:
            return None
        
        base = results[0]['per_100g']
        ratio = grams / 100.0
        
        return {
            'name': results[0]['name'],
            'grams': grams,
            'nutrients': {
                'calories': round(base['calories'] * ratio, 1),
                'protein': round(base['protein'] * ratio, 1),
                'carbs': round(base['carbs'] * ratio, 1),
                'fat': round(base['fat'] * ratio, 1),
                'sodium': round(base['sodium'] * ratio, 1),
                'fiber': round(base['fiber'] * ratio, 1),
                'potassium': round(base['potassium'] * ratio, 1),
            }
        }
    
    def get_categories(self) -> List[str]:
        """取得所有食品分類"""
        if 'category' in self.simplified_df.columns:
            return sorted(self.simplified_df['category'].dropna().unique().tolist())
        return []
    
    def get_stats(self) -> Dict[str, Any]:
        """取得服務統計資訊"""
        match_rate = 0
        if self._search_stats['total_queries'] > 0:
            match_rate = (
                self._search_stats['successful_matches'] / 
                self._search_stats['total_queries'] * 100
            )
        
        # 確保資料已載入
        _ = self.simplified_df
        
        return {
            'total_foods': len(self._simplified_df) if self._simplified_df is not None else 0,
            'total_categories': len(self.get_categories()),
            'queries': self._search_stats.copy(),
            'match_rate_percent': round(match_rate, 1),
            'status': 'healthy' if self._df is not None and len(self._df) > 0 else 'no_data'
        }
    
    def validate_top20_foods(self) -> Dict[str, Any]:
        """
        驗證 Top 20 常見食物的匹配率
        這是 Phase 1 的核心成功指標
        """
        test_foods = [
            '白飯', '糙米飯', '麵條', '吐司', '饅頭',  # 主食
            '雞胸肉', '雞蛋', '豆腐', '鮭魚', '豬肉',  # 蛋白質
            '菠菜', '高麗菜', '花椰菜', '番茄', '紅蘿蔔',  # 蔬菜
            '蘋果', '香蕉', '柳橙', '芭樂', '奇異果',  # 水果
        ]
        
        results = []
        for food in test_foods:
            matches = self.search(food, limit=1)
            results.append({
                'query': food,
                'matched': len(matches) > 0,
                'matched_name': matches[0]['name'] if matches else None,
            })
        
        matched_count = sum(1 for r in results if r['matched'])
        match_rate = matched_count / len(test_foods) * 100
        
        return {
            'test_count': len(test_foods),
            'matched_count': matched_count,
            'match_rate_percent': round(match_rate, 1),
            'target_rate_percent': 80,  # 目標 ≥ 80%
            'passed': match_rate >= 80,
            'details': results,
        }


# 全域單例（延遲初始化）
_nutrition_service: Optional[NutritionDBService] = None


def get_nutrition_service() -> NutritionDBService:
    """取得營養服務單例"""
    global _nutrition_service
    if _nutrition_service is None:
        _nutrition_service = NutritionDBService()
    return _nutrition_service
