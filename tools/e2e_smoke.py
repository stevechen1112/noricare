import uuid
import httpx

BASE_URL = "http://localhost:8001/api/v1"


def main() -> int:
    email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    password = "pass1234"
    name = "Test"

    r = httpx.post(f"{BASE_URL}/auth/register", json={"email": email, "password": password, "name": name})
    print("register", r.status_code)
    if r.status_code != 200:
        print(r.text)
        return 1

    data = r.json()
    token = data.get("access_token") or data.get("token")
    headers = {"Authorization": f"Bearer {token}"}

    me = httpx.get(f"{BASE_URL}/auth/me", headers=headers)
    print("me", me.status_code)
    if me.status_code != 200:
        print(me.text)
        return 1

    align = httpx.get(f"{BASE_URL}/food/align", params={"q": "雞胸肉", "limit": 1})
    print("align", align.status_code)
    if align.status_code != 200:
        print(align.text)
        return 1

    food_id = (align.json().get("results") or [{}])[0].get("food_id")
    meal = httpx.post(
        f"{BASE_URL}/meals",
        headers=headers,
        json={
            "items": [
                {
                    "food_id": food_id,
                    "grams": 120,
                    "portion_label": "manual",
                    "raw_text": "雞胸肉",
                }
            ],
            "source": "manual",
        },
    )
    print("create meal", meal.status_code)
    if meal.status_code != 200:
        print(meal.text)
        return 1

    summary = httpx.get(f"{BASE_URL}/meals/summary", headers=headers, params={"days": 7})
    print("summary", summary.status_code)
    if summary.status_code != 200:
        print(summary.text)
        return 1

    recent = httpx.get(f"{BASE_URL}/meals", headers=headers, params={"limit": 5})
    print("list", recent.status_code)
    if recent.status_code != 200:
        print(recent.text)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
