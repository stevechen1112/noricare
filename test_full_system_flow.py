import httpx
import time
import os
import json

API_BASE_URL = "http://localhost:8001/api/v1"
TEST_IMAGE = r"c:\Users\User\Desktop\personalhealth\steve_personaldata\40108.jpg"

def test_full_flow():
    with httpx.Client() as client:
        # 1. Create User Profile
        print("1. Creating User Profile...")
        user_payload = {
            "name": "AI Tester",
            "age": 35,
            "gender": "male",
            "height_cm": 175,
            "weight_kg": 70,
            "health_goals": ["增肌", "減脂"],
            "lifestyle": {
                "activity_level": "moderate",
                "dietary_preference": "none",
                "eating_habits": ["三餐定時"],
                "allergies": []
            }
        }
        resp = client.post(f"{API_BASE_URL}/users/", json=user_payload, timeout=10.0)
        if resp.status_code != 200:
            print(f"User creation failed: {resp.text}")
            # Try without ID if that's the issue (create usually generates it)
            return
        
        user_data = resp.json()
        print(f"User creation successful. ID: {user_data.get('id')}")

        # 2. Upload OCR
        print(f"\n2. Uploading {TEST_IMAGE}...")
        with open(TEST_IMAGE, "rb") as f:
            files = {"file": ("report.jpg", f, "image/jpeg")}
            resp = client.post(f"{API_BASE_URL}/ocr/upload", files=files, timeout=30.0)
        
        if resp.status_code != 200:
            print(f"OCR Upload failed: {resp.text}")
            return
        
        file_id = resp.json().get("file_id")
        print(f"OCR Uploaded, file_id: {file_id}")

        # 3. Poll OCR
        print("Polling OCR result...")
        ocr_result = None
        for i in range(20):
            time.sleep(2)
            try:
                res_resp = client.get(f"{API_BASE_URL}/ocr/result/{file_id}", timeout=60.0)
            except httpx.ReadTimeout:
                if i == 19:
                    print("OCR polling timed out.")
                continue

            if res_resp.status_code == 200:
                res_data = res_resp.json()
                if res_data["status"] == "completed":
                    ocr_result = res_data["data"]
                    print("OCR Completed.")
                    break
        
        if not ocr_result:
            print("OCR Timeout.")
            return

        # 4. Generate Recommendation
        print("\n3. Generating Recommendation (This may take 10-20s)...")
        # Extract names like the frontend does
        abnormal_names = []
        for item in ocr_result.get("abnormal_items", []):
            if isinstance(item, dict) and "name" in item:
                abnormal_names.append(item["name"])
            else:
                abnormal_names.append(str(item))

        rec_payload = {
            "user_profile": user_data,
            "health_data": ocr_result["structured_data"],
            "abnormal_items": abnormal_names
        }
        
        rec_start = time.time()
        rec_resp = client.post(f"{API_BASE_URL}/recommendation/generate", json=rec_payload, timeout=60.0)
        rec_duration = time.time() - rec_start
        
        if rec_resp.status_code == 200:
            print(f"SUCCESS: Recommendation successfully generated in {rec_duration:.1f}s!")
            report = rec_resp.json()
            print(f"Report ID: {report.get('report_id')}")
            print(f"Health Score: {report.get('health_score')}")
        else:
            print(f"FAILED: Recommendation failed: {rec_resp.status_code} - {rec_resp.text}")

        # 5. Nutrition Database Test
        print("\n4. Testing Nutrition Database...")
        nut_resp = client.get(f"{API_BASE_URL}/nutrition/search", params={"q": "雞胸肉"})
        if nut_resp.status_code == 200:
            nut_data = nut_resp.json()
            print(f"SUCCESS: Nutrition search works! Found {nut_data.get('count')} items.")
        else:
            print(f"FAILED: Nutrition search failed: {nut_resp.text}")

if __name__ == "__main__":
    test_full_flow()
