import shutil
import os
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from typing import List, Dict
from uuid import uuid4
from app.services.ocr_service import ocr_service

router = APIRouter()

UPLOAD_DIR = "uploads"
# 暫時用記憶體存放結果，MVP 之後會進 DB (Sprint 2)
RESULTS_CACHE: Dict[str, dict] = {}

@router.post("/upload")
async def upload_health_report(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """
    上傳健檢報告圖片，返回暫存 ID 並觸發 OCR 流程 (Sprint 1)
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="僅支援圖片格式上傳")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_id = str(uuid4())
    file_ext = os.path.splitext(file.filename)[1]
    save_path = os.path.join(UPLOAD_DIR, f"{file_id}{file_ext}")

    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # 建立初始狀態
    RESULTS_CACHE[file_id] = {"status": "processing", "data": None}
    
    # 異步執行 OCR
    background_tasks.add_task(run_ocr_and_save, file_id, save_path)
    
    return {
        "file_id": file_id,
        "filename": file.filename,
        "status": "upload_success_and_processing"
    }

async def run_ocr_and_save(file_id: str, file_path: str):
    result = await ocr_service.process_image(file_path)
    RESULTS_CACHE[file_id] = {"status": "completed", "data": result}

@router.get("/result/{file_id}")
async def get_ocr_result(file_id: str):
    """
    獲取 OCR 處理結果 (Sprint 1-2)
    """
    if file_id not in RESULTS_CACHE:
        raise HTTPException(status_code=404, detail="找不到該專案或已過期")
    
    return RESULTS_CACHE[file_id]
