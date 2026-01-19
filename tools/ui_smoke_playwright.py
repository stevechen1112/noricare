from playwright.sync_api import sync_playwright

URL = "http://localhost:8080"
OUT = "ui_smoke_flutter_web.png"


def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(URL, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(5000)
        page.screenshot(path=OUT, full_page=True)
        browser.close()
    print(f"Saved screenshot: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
