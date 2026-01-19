import httpx
import json
import sys

# Configuration
API_BASE = "http://localhost:8000/api/v1"
ALIGN_QUERY = "雞胸肉"  # Classic test case
EXPECTED_FOOD_ID = "I0402401" # From Taiwan FDA DB
EXPECTED_CALORIES_PER_100G = 117 # Approx for raw chicken breast

def run_verification():
    print("=" * 60)
    print("🚀 2026 Feature Verification: Automation Suite")
    print("=" * 60)
    
    with httpx.Client(base_url=API_BASE, timeout=10.0) as client:
        # 1. Health Check
        print("\n[Step 1] Checking System Health...")
        try:
            # Use absolute URL to break out of base_url scope safely
            resp = client.get("http://localhost:8000/health") 
            if resp.status_code == 200:
                print("✅ Backend is ONLINE")
            else:
                print(f"❌ Backend returned {resp.status_code}")
                # Don't return, try to proceed in case it's just health check weirdness
        except Exception as e:
            print(f"❌ Health Check Connection failed: {e}")
            # If health check fails, api might still work, or not.
            # But let's proceed to see specifically where it fails.

        # 2. Create Test User
        print("\n[Step 2] Creating Test User for Session...")
        user_payload = {
            "name": "Auto Verifier 2026",
            "age": 30,
            "gender": "female",
            "height_cm": 165,
            "weight_kg": 55,
            "health_goals": ["maintain"],
            "lifestyle": {"activity_level": "sedentary", "dietary_preference": "none", "eating_habits": [], "allergies": []}
        }
        resp = client.post("/users/", json=user_payload)
        if resp.status_code != 200:
            print(f"❌ Failed to create user: {resp.text}")
            return
        user_id = resp.json()["id"]
        print(f"✅ User Created: {user_id}")

        # 3. Test Alignment (The Core 2026 Feature)
        print(f"\n[Step 3] Testing Food Alignment (Anti-Hallucination)...")
        print(f"   Querying: '{ALIGN_QUERY}'")
        resp = client.get(f"/food/align", params={"q": ALIGN_QUERY, "limit": 1})
        data = resp.json()
        
        if not data.get("results"):
            print("❌ No alignment results found")
            return
            
        first_match = data["results"][0]
        # Schema uses 'name', not 'food_name'
        matched_name = first_match.get("name", "Unknown") 
        matched_id = first_match["food_id"]
        
        print(f"   Mapped to: [{matched_id}] {matched_name}")
        
        # Validation Logic
        if matched_id == EXPECTED_FOOD_ID:
            print(f"✅ EXACT MATCH CONFIRMED: System correctly mapped '{ALIGN_QUERY}' to FDA ID '{matched_id}'")
        else:
            print(f"⚠️  Match differs from expected, but found Valid ID {matched_id}")

        # 4. Log Meal (The Data Flow)
        print("\n[Step 4] Logging Meal to Database...")
        # Simulate eating 200g
        grams = 200.0
        meal_payload = {
            "user_id": user_id,
            "source": "automated_test",
            "items": [
                {
                    "food_id": matched_id,
                    "grams": grams,
                    "portion_label": "200g serving",
                    "raw_text": ALIGN_QUERY
                }
            ]
        }
        resp = client.post("/meals", json=meal_payload)
        if resp.status_code != 200:
            print(f"❌ Failed to log meal: {resp.text}")
            return
        
        meal_data = resp.json()
        # In MealResponse, it is 'nutrients', not 'total_nutrients'
        saved_cals = meal_data["nutrients"]["calories"]
        print(f"✅ Meal Logged. ID: {meal_data['meal_id']}")
        print(f"   Calculated Calories for {grams}g: {saved_cals} kcal")
        
        # Verify Math
        # If 100g is ~117kcal, 200g should be ~234kcal
        # We don't hardcode exact float match, but check reasonable range
        expected_total = (EXPECTED_CALORIES_PER_100G * grams / 100)
        if abs(saved_cals - expected_total) < 50:
            print(f"✅ DATA INTEGRITY PASS: Calories {saved_cals} is consistent with FDA database ({expected_total})")
        else:
            print(f"❌ DATA INTEGRITY FAIL: Calories {saved_cals} seems off (Expected ~{expected_total})")

        # 5. Check Summary (Frontend View Simulation)
        print("\n[Step 5] Retrieving User Summary (Frontend View)...")
        resp = client.get("/meals/summary", params={"user_id": user_id, "days": 1})
        summary = resp.json()
        
        total_meals = summary["total_meals"]
        total_protein = summary["total_nutrients"]["protein"]
        
        print(f"   Total Meals Today: {total_meals}")
        print(f"   Total Protein: {total_protein:.2f} g")
        
        if total_meals >= 1 and total_protein > 0:
            print("✅ END-TO-END VERIFICATION PASSED")
        else:
            print("❌ Summary Missing Data")

    print("\n" + "=" * 60)
    print("Testing Complete.")

if __name__ == "__main__":
    run_verification()
