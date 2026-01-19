from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.endpoints import ocr, recommendation, users, chat, auth, nutrition, food, meals

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="結合 OCR 與營養建議的健康管理系統 - Powered by Gemini 3 Pro",
    version="0.2.0 (Refactored)",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# 設定 CORS (為了未來的前端 UI)
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

@app.get("/")
async def root():
    return {
        "message": "Welcome to Personal Health AI Agent API",
        "doc_url": "/docs",
        "status": "active"
    }

@app.get("/health")
async def health_check():
    return {"status": "ok", "gemini_model": settings.GEMINI_MODEL_NAME}

# Router 註冊
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(ocr.router, prefix="/api/v1/ocr", tags=["OCR"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(recommendation.router, prefix="/api/v1/recommendation", tags=["Recommendation"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(nutrition.router, prefix="/api/v1", tags=["Nutrition"])  # 獨立營養查詢 API
app.include_router(food.router, prefix="/api/v1", tags=["Food"])  # 食物名稱對齊 API
app.include_router(meals.router, prefix="/api/v1", tags=["Meals"])  # 飲食紀錄 API

