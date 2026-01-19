"""測試完整流程的腳本"""
import httpx
import asyncio
import json

API_BASE = "http://localhost:8000/api/v1"

async def test_complete_flow():
    print("=" * 60)
    print("🧪 Personal Health - 完整流程測試")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. 健康檢查
        print("\n1️⃣ 測試後端健康狀態...")
        try:
            health_resp = await client.get("http://localhost:8000/health")
            health = health_resp.json()
            print(f"   ✅ 後端狀態: {health['status']}")
            print(f"   ✅ 模型: {health['gemini_model']}")
        except Exception as e:
            print(f"   ❌ 後端連線失敗: {e}")
            return
        
        # 2. 創建用戶
        print("\n2️⃣ 測試創建用戶...")
        user_payload = {
            "name": "測試用戶",
            "age": 35,
            "gender": "male",
            "height_cm": 175.0,
            "weight_kg": 70.0,
            "health_goals": ["減重", "控制血糖"],
            "lifestyle": {
                "activity_level": "moderate",
                "dietary_preference": "無特殊偏好",
                "eating_habits": ["外食族"],
                "allergies": []
            }
        }
        
        try:
            user_resp = await client.post(f"{API_BASE}/users/", json=user_payload)
            if user_resp.status_code == 200:
                user = user_resp.json()
                print(f"   ✅ 用戶創建成功")
                print(f"   📝 ID: {user['id']}")
                print(f"   👤 姓名: {user['name']}")
                print(f"   📊 BMI: {user['bmi']:.2f}")
            else:
                print(f"   ❌ 創建失敗: {user_resp.status_code} - {user_resp.text}")
                return
        except Exception as e:
            print(f"   ❌ API 調用失敗: {e}")
            return
        
        # 3. 測試營養查詢
        print("\n3️⃣ 測試營養資料庫查詢...")
        try:
            nutrition_resp = await client.get(f"{API_BASE}/nutrition/search", params={"query": "雞胸肉"})
            if nutrition_resp.status_code == 200:
                results = nutrition_resp.json()
                print(f"   ✅ 找到 {len(results)} 筆結果")
                if results:
                    first = results[0]
                    print(f"   🍗 {first['name']}")
                    print(f"      熱量: {first.get('calories', 'N/A')} kcal")
                    print(f"      蛋白質: {first.get('protein', 'N/A')} g")
            else:
                print(f"   ⚠️ 查詢狀態: {nutrition_resp.status_code}")
        except Exception as e:
            print(f"   ❌ 營養查詢失敗: {e}")
        
        # 4. 測試 Streamlit
        print("\n4️⃣ 測試 Streamlit Web UI...")
        try:
            streamlit_resp = await client.get("http://localhost:8501")
            if streamlit_resp.status_code == 200:
                print(f"   ✅ Streamlit 運行正常")
                print(f"   🌐 URL: http://localhost:8501")
            else:
                print(f"   ⚠️ Streamlit 狀態: {streamlit_resp.status_code}")
        except Exception as e:
            print(f"   ❌ Streamlit 連線失敗: {e}")
    
    print("\n" + "=" * 60)
    print("✅ 測試完成！")
    print("=" * 60)
    print("\n📍 你可以現在開始使用:")
    print("   • Streamlit Web UI: http://localhost:8501")
    print("   • Backend API Docs: http://localhost:8000/docs")
    print("   • Backend Health: http://localhost:8000/health")

if __name__ == "__main__":
    asyncio.run(test_complete_flow())
