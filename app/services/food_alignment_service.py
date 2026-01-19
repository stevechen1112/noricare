"""
Food Alignment Service
======================
將食物文字名稱對齊到營養資料庫的整合編號。
"""

from __future__ import annotations

import os
import re
from typing import Dict, List, Optional, Any
from functools import lru_cache
from difflib import SequenceMatcher

import pandas as pd

from app.services.nutrition_db_service import get_nutrition_service


class FoodAlignmentService:
    """食物名稱對齊服務（MVP）"""

    REQUIRED_FIELDS = [
        "整合編號",
        "食品分類",
        "樣品名稱",
        "內容物描述",
        "俗名",
        "熱量(kcal)",
        "粗蛋白(g)",
        "總碳水化合物(g)",
        "粗脂肪(g)",
        "鈉(mg)",
        "膳食纖維(g)",
        "鉀(mg)",
    ]

    NUMERIC_FIELDS = [
        "熱量(kcal)",
        "粗蛋白(g)",
        "總碳水化合物(g)",
        "粗脂肪(g)",
        "鈉(mg)",
        "膳食纖維(g)",
        "鉀(mg)",
    ]

    def __init__(self, csv_path: Optional[str] = None) -> None:
        if csv_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            csv_path = os.path.join(base_dir, "食品營養成分資料庫2024UPDATE2_clean.csv")
            if not os.path.exists(csv_path):
                csv_path = "食品營養成分資料庫2024UPDATE2_clean.csv"
        self.csv_path = csv_path
        self._df: Optional[pd.DataFrame] = None
        self._index: Optional[List[Dict[str, Any]]] = None

    @property
    def df(self) -> pd.DataFrame:
        if self._df is None:
            self._load_data()
        return self._df

    def _load_data(self) -> None:
        self._df = pd.read_csv(self.csv_path, encoding="utf-8")
        for col in self.NUMERIC_FIELDS:
            if col in self._df.columns:
                self._df[col] = pd.to_numeric(self._df[col], errors="coerce").fillna(0)

    def _build_index(self) -> None:
        if self._index is not None:
            return
        self._index = []
        df = self.df
        for _, row in df.iterrows():
            record = {
                "food_id": str(row.get("整合編號", "")),
                "category": str(row.get("食品分類", "")),
                "name": str(row.get("樣品名稱", "")),
                "alias": self._split_aliases(row.get("俗名", "")) + self._split_aliases(row.get("內容物描述", "")),
                "name_norm": self._normalize(str(row.get("樣品名稱", ""))),
            }
            record["alias_norm"] = [self._normalize(a) for a in record["alias"] if a]
            self._index.append(record)

    @staticmethod
    def _split_aliases(value: Any) -> List[str]:
        if value is None:
            return []
        text = str(value)
        if not text or text == "nan":
            return []
        parts = re.split(r"[，,;/、\n\r]+", text)
        return [p.strip().strip("\"") for p in parts if p.strip()]

    @staticmethod
    def _normalize(text: str) -> str:
        if not text:
            return ""
        text = text.lower().strip()
        text = re.sub(r"\([^\)]*\)", "", text)
        text = re.sub(r"[\s\-_/]+", "", text)
        text = re.sub(r"[\[\]{}<>]", "", text)
        return text

    @staticmethod
    def _score(query_norm: str, candidate_norm: str) -> float:
        if not query_norm or not candidate_norm:
            return 0.0
        if query_norm == candidate_norm:
            return 1.0
        if query_norm in candidate_norm:
            return 0.85
        return SequenceMatcher(None, query_norm, candidate_norm).ratio()

    def align(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        self._build_index()
        query_norm = self._normalize(query)
        results: List[Dict[str, Any]] = []

        for record in self._index or []:
            name_score = self._score(query_norm, record["name_norm"])
            alias_scores = [self._score(query_norm, a) for a in record.get("alias_norm", [])]
            best_alias_score = max(alias_scores) if alias_scores else 0.0

            best_score = max(name_score, best_alias_score)
            if best_score <= 0:
                continue

            matched_field = "name" if name_score >= best_alias_score else "alias"
            results.append({
                "food_id": record["food_id"],
                "name": record["name"],
                "category": record["category"],
                "matched_field": matched_field,
                "score": round(best_score, 4),
            })

        results.sort(key=lambda r: r["score"], reverse=True)
        return results[:limit]

    def get_food_nutrients(self, food_id: str) -> Optional[Dict[str, Any]]:
        if not food_id:
            return None
        df = self.df
        match = df[df["整合編號"].astype(str) == str(food_id)]
        if match.empty:
            return None
        row = match.iloc[0]
        return {
            "food_id": str(row.get("整合編號", "")),
            "name": str(row.get("樣品名稱", "")),
            "category": str(row.get("食品分類", "")),
            "per_100g": {
                "calories": float(row.get("熱量(kcal)", 0) or 0),
                "protein": float(row.get("粗蛋白(g)", 0) or 0),
                "carbs": float(row.get("總碳水化合物(g)", 0) or 0),
                "fat": float(row.get("粗脂肪(g)", 0) or 0),
                "sodium": float(row.get("鈉(mg)", 0) or 0),
                "fiber": float(row.get("膳食纖維(g)", 0) or 0),
                "potassium": float(row.get("鉀(mg)", 0) or 0),
            }
        }


@lru_cache(maxsize=1)
def get_food_alignment_service() -> FoodAlignmentService:
    return FoodAlignmentService()
