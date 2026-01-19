from playwright.sync_api import sync_playwright, expect

APP_URL = "http://localhost:8501"


def run_ui_smoke():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # 1) Open app
        page.goto(APP_URL, wait_until="networkidle")
        expect(page.get_by_text("個人專屬營養師 AI Agent")).to_be_visible()

        # 2) Step 1: Create user (use defaults, just click next)
        page.get_by_role("button", name="下一步：上傳報告 ➡️").click()
        expect(page.get_by_text("上傳您的最新健檢報告")).to_be_visible()

        # 3) Navigate to Step 5 via sidebar
        page.get_by_test_id("stSidebarUserContent").get_by_role("button", name="🍱 飲食紀錄").click()
        expect(page.get_by_text("飲食紀錄與營養加總")).to_be_visible()

        # 4) Add a meal
        page.get_by_label("輸入食物名稱").fill("雞胸肉")
        grams_input = page.get_by_label("份量(g)")
        grams_input.fill("150")
        page.get_by_role("button", name="🔍 對齊").click()

        # Wait for alignment results and select first option
        expect(page.get_by_text("選擇匹配結果")).to_be_visible()
        combo = page.get_by_test_id("stMainBlockContainer").get_by_role("combobox").first
        combo.click()
        page.keyboard.press("ArrowDown")
        page.keyboard.press("Enter")
        add_btn = page.get_by_role("button", name="➕ 加入餐點")
        expect(add_btn).to_be_visible()
        add_btn.click()
        expect(page.get_by_text("已加入餐點清單")).to_be_visible(timeout=15000)
        expect(page.get_by_text("🧾 餐點清單")).to_be_visible(timeout=15000)

        # Save meal
        page.get_by_test_id("stMainBlockContainer").get_by_role("button", name="✅ 儲存這一餐").click()
        expect(page.get_by_text("餐點已儲存")).to_be_visible()

        # Check summary appears
        expect(page.get_by_text("近 7 日營養總結")).to_be_visible()

        browser.close()


if __name__ == "__main__":
    run_ui_smoke()
