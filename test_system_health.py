import httpx
import time
import os
import json

API_BASE_URL = "http://localhost:8001/api/v1"
TEST_IMAGE = r"c:\Users\User\Desktop\personalhealth\steve_personaldata\40108.jpg"

def test_ocr_flow():
    if not os.path.exists(TEST_IMAGE):
        print(f"Test image not found at {TEST_IMAGE}")
        return

    with httpx.Client(timeout=60.0) as client:
        # 1. Upload
        print(f"Uploading {TEST_IMAGE}...")
        with open(TEST_IMAGE, "rb") as f:
            files = {"file": ("report.jpg", f, "image/jpeg")}
            resp = client.post(f"{API_BASE_URL}/ocr/upload", files=files)
        
        if resp.status_code != 200:
            print(f"Upload failed: {resp.status_code} - {resp.text}")
            return
        
        data = resp.json()
        file_id = data.get("file_id")
        print(f"Upload successful, file_id: {file_id}")

        # 2. Poll result
        print("Polling for result...")
        for _ in range(15):
            time.sleep(2)
            res_resp = client.get(f"{API_BASE_URL}/ocr/result/{file_id}")
            if res_resp.status_code == 200:
                res_data = res_resp.json()
                status = res_data.get("status")
                print(f"Status: {status}")
                if status == "completed":
                    ocr_result = res_data.get("data")
                    print("\n--- OCR Result Details ---")
                    print(f"Keys in result: {list(ocr_result.keys())}")
                    
                    if "structured_data" in ocr_result:
                        print("✅ Found 'structured_data'")
                        print(f"Structured Data Keys: {list(ocr_result['structured_data'].keys())}")
                    else:
                        print("❌ MISSING 'structured_data'")
                    
                    if "abnormal_items" in ocr_result:
                        print("✅ Found 'abnormal_items'")
                        print(f"Abnormal Items: {ocr_result['abnormal_items']}")
                    else:
                        print("❌ MISSING 'abnormal_items'")
                    
                    return
                elif status == "failed":
                    print("OCR Failed")
                    return
            else:
                print(f"Error polling: {res_resp.status_code}")
                break
        print("OCR Timeout")

if __name__ == "__main__":
    test_ocr_flow()
