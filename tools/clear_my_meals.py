"""
Clear all meals for current logged-in user
用法: python clear_my_meals.py <jwt_token>
"""
import sys
import requests

if len(sys.argv) < 2:
    print("Usage: python clear_my_meals.py <jwt_token>")
    print("\nGet your JWT token from:")
    print("1. Open https://noricare.app")
    print("2. Press F12 (DevTools)")
    print("3. Go to Application > Local Storage")
    print("4. Copy the auth token value")
    sys.exit(1)

token = sys.argv[1]
base_url = "https://noricare.app/api/v1"

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# 1. Get all meals
print("Fetching your meals...")
response = requests.get(f"{base_url}/meals", headers=headers)

if response.status_code == 401:
    print("❌ Token invalid or expired. Please get a new token.")
    sys.exit(1)

if response.status_code != 200:
    print(f"❌ Error fetching meals: {response.status_code}")
    print(response.text)
    sys.exit(1)

meals = response.json()
print(f"Found {len(meals)} meals")

if len(meals) == 0:
    print("✓ No meals to delete")
    sys.exit(0)

# 2. Ask for confirmation
print("\nMeals to delete:")
for i, meal in enumerate(meals, 1):
    print(f"{i}. {meal['eaten_at']} - {len(meal['items'])} items")

confirm = input(f"\nDelete all {len(meals)} meals? (yes/no): ")
if confirm.lower() not in ['yes', 'y']:
    print("Cancelled")
    sys.exit(0)

# 3. Delete each meal
deleted = 0
failed = 0
for meal in meals:
    meal_id = meal['meal_id']
    response = requests.delete(f"{base_url}/meals/{meal_id}", headers=headers)
    if response.status_code == 200:
        deleted += 1
        print(f"✓ Deleted meal {meal_id}")
    else:
        failed += 1
        print(f"✗ Failed to delete {meal_id}: {response.status_code}")

print(f"\n=== Summary ===")
print(f"Deleted: {deleted}")
print(f"Failed: {failed}")
print(f"Total: {len(meals)}")
