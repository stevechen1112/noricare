# 初始化資料庫腳本
from app.db.session import engine, Base
from app.models.all_models import User, HealthRecord, Meal, MealItem, AuthAccount

def init_db():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    init_db()
