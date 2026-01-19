from sqlalchemy import Column, Integer, String, Float, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    name = Column(String, index=True)
    age = Column(Integer)
    gender = Column(String)
    height_cm = Column(Float)
    weight_kg = Column(Float)
    
    # 儲存生活型態與問卷資料 (JSON)
    # 包含: dietary_preference, allergies, activity_level, eating_habits, budget_level
    lifestyle_data = Column(JSON, default=dict)
    
    # 健康目標 (JSON list)
    health_goals = Column(JSON, default=list)

    def __init__(self, **kwargs):
      # Handle 'lifestyle' to 'lifestyle_data' mapping if needed or just use kwargs
      super().__init__(**kwargs)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 關聯：一個使用者有多筆健康紀錄
    records = relationship("HealthRecord", back_populates="owner")
    meals = relationship("Meal", back_populates="owner")


class AuthAccount(Base):
    """Email+password auth account.

    Separates credentials from the health profile (`users` table) to avoid
    forcing immediate profile onboarding at registration time.
    """

    __tablename__ = "auth_accounts"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    password_hash = Column(String, nullable=False)

    # Optional link to an existing health profile
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    profile = relationship("User")

    created_at = Column(DateTime(timezone=True), server_default=func.now())

class HealthRecord(Base):
    """
    儲存每一次的上傳與分析結果
    這是做「趨勢分析」的基石
    """
    __tablename__ = "health_records"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    
    # 原始圖片 (可選)
    image_path = Column(String, nullable=True)
    
    # OCR 識別結果 (儲存 raw_ocr_output)
    # 結構: {"GLUCOSE": {"value": 100, ...}, "HbA1c": ...}
    clinical_data = Column(JSON, default=dict)
    
    # AI 分析報告 (儲存 nutrition_report)
    # 結構: {"food_advice": ..., "supplement_advice": ...}
    ai_analysis = Column(JSON, default=dict)
    
    # 異常項目快照
    abnormal_items = Column(JSON, default=list)

    # 綜合評分
    health_score = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="records")


class Meal(Base):
    """
    使用者飲食紀錄（每一餐）
    """
    __tablename__ = "meals"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    user_id = Column(String, ForeignKey("users.id"))

    source = Column(String, default="manual")
    note = Column(String, nullable=True)
    eaten_at = Column(DateTime(timezone=True), server_default=func.now())

    nutrients = Column(JSON, default=dict)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="meals")
    items = relationship("MealItem", back_populates="meal")


class MealItem(Base):
    """
    一餐中的食物項目
    """
    __tablename__ = "meal_items"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    meal_id = Column(String, ForeignKey("meals.id"))

    food_id = Column(String, index=True)
    food_name = Column(String, index=True)
    grams = Column(Float)
    portion_label = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)
    raw_text = Column(String, nullable=True)

    nutrients = Column(JSON, default=dict)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    meal = relationship("Meal", back_populates="items")
