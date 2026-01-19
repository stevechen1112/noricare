#!/usr/bin/env python
"""啟動後端 API 的獨立腳本"""
import uvicorn
import os

if __name__ == "__main__":
    print("=" * 60)
    print("[ROCKET] Personal Health Backend API")
    print("=" * 60)
    print("[PIN] URL: http://localhost:8000")
    print("[BOOK] API Docs: http://localhost:8000/docs")
    print("=" * 60)
    
    # 確保在正確的目錄
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # 啟動服務
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["app"],
        log_level="info"
    )
